from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Max, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categoria, EventoTimeline, Fuente, Gobierno, Indicador, IndicadorValor, Medio, Noticia, PulsoIndexSnapshot
from .services import pulso_index
from .serializers import (
    CategoriaSerializer,
    EventoTimelineSerializer,
    FuenteSerializer,
    GobiernoSerializer,
    IndicadorSerializer,
    IndicadorValorSerializer,
    MedioSerializer,
    NoticiaSerializer,
)


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class FuenteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Fuente.objects.all()
    serializer_class = FuenteSerializer


class IndicadorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Indicador.objects.select_related('categoria', 'fuente').all()
    serializer_class = IndicadorSerializer
    filterset_fields = ['categoria', 'destacado', 'tipo', 'actualizacion_automatica']


class IndicadorValorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IndicadorValor.objects.select_related('indicador').all()
    serializer_class = IndicadorValorSerializer
    filterset_fields = ['indicador', 'granularidad']
    ordering_fields = ['fecha']


class EventoTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventoTimeline.objects.select_related('categoria', 'fuente').all()
    serializer_class = EventoTimelineSerializer
    filterset_fields = ['categoria', 'sentimiento']


class NoticiaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NoticiaSerializer
    filterset_fields = ['categoria', 'publicado']

    def get_queryset(self):
        qs = Noticia.objects.select_related('categoria', 'medio').all()
        # Igual que la política RLS del SQL original: sin filtro explícito de
        # "publicado", el público solo ve las publicadas.
        if 'publicado' not in self.request.query_params:
            qs = qs.filter(publicado=True)
        return qs


class UltimosValoresView(APIView):
    """Equivalente a la vista SQL `ultimos_valores`: el último valor cargado
    de cada indicador por granularidad — lo que pinta las tarjetas."""

    def get(self, request):
        latest = (
            IndicadorValor.objects.values('indicador_id', 'granularidad')
            .annotate(max_fecha=Max('fecha'))
        )
        query = Q()
        for row in latest:
            query |= Q(
                indicador_id=row['indicador_id'],
                granularidad=row['granularidad'],
                fecha=row['max_fecha'],
            )
        queryset = IndicadorValor.objects.filter(query) if latest else IndicadorValor.objects.none()

        indicador_id = request.query_params.get('indicador_id')
        if indicador_id:
            queryset = queryset.filter(indicador_id=indicador_id)
        granularidad = request.query_params.get('granularidad')
        if granularidad:
            queryset = queryset.filter(granularidad=granularidad)

        serializer = IndicadorValorSerializer(queryset, many=True)
        return Response(serializer.data)


class TimelineResumenMensualView(APIView):
    """Equivalente a la vista SQL `timeline_resumen_mensual`: conteo de
    eventos positivos/negativos/neutros por mes."""

    def get(self, request):
        resumen = (
            EventoTimeline.objects.annotate(mes=TruncMonth('fecha'))
            .values('mes', 'sentimiento')
            .annotate(cantidad=Count('id'))
            .order_by('-mes', 'sentimiento')
        )
        return Response(list(resumen))


def _to_decimal(texto):
    """Extrae el primer número de un delta_texto tipo '-42pp vs. año anterior'."""
    if not texto:
        return None
    signo = '-' if '-' in texto else ''
    digitos = ''.join(c for c in texto if c.isdigit() or c == '.')
    if not digitos:
        return None
    try:
        return Decimal(signo + digitos)
    except InvalidOperation:
        return None


class DestacadosView(APIView):
    """Dólar oficial, dólar blue y Merval — los tres valores que van arriba de
    todo en el header, más la brecha cambiaria ya calculada."""

    IDS_DESTACADOS = ['dolar_oficial', 'dolar_blue', 'merval']

    def get(self, request):
        valores = {}
        for indicador_id in self.IDS_DESTACADOS:
            ultimo = (
                IndicadorValor.objects.filter(indicador_id=indicador_id, granularidad='dia')
                .order_by('-fecha')
                .first()
            )
            if ultimo:
                valores[indicador_id] = {
                    'valor': ultimo.valor_numerico,
                    'delta': _to_decimal(ultimo.delta_texto) or Decimal('0'),
                    'fecha': ultimo.fecha,
                }

        data = {
            'dolares': {
                'oficial': valores.get('dolar_oficial'),
                'blue': valores.get('dolar_blue'),
            },
            'merval': valores.get('merval'),
        }

        oficial = valores.get('dolar_oficial')
        blue = valores.get('dolar_blue')
        if oficial and blue and oficial['valor']:
            data['brecha'] = round(((blue['valor'] - oficial['valor']) / oficial['valor']) * 100)
        else:
            data['brecha'] = None

        return Response(data)


class MedioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medio.objects.all()
    serializer_class = MedioSerializer
    filterset_fields = ['tipo', 'orientacion']


class GobiernoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Gobierno.objects.all()
    serializer_class = GobiernoSerializer


def _resumir_indicador(indicador, desde, hasta):
    """Resume un indicador dentro de [desde, hasta]: valor al inicio, valor
    al final, variación y promedio. Si el indicador tiene puntos en más de
    una granularidad dentro del rango, usa la que tenga más puntos (la más
    "nativa" para ese período) en vez de mezclarlas."""
    valores = list(IndicadorValor.objects.filter(indicador=indicador, fecha__gte=desde, fecha__lte=hasta))
    base = {
        'id': indicador.id,
        'nombre': indicador.nombre,
        'categoria_id': indicador.categoria_id,
        'tipo': indicador.tipo,
        'unidad': indicador.unidad,
        'polaridad': indicador.polaridad,
        'fuente': {'nombre': indicador.fuente.nombre, 'url': indicador.fuente.url} if indicador.fuente else None,
    }
    if not valores:
        return {**base, 'sin_datos': True}

    granularidad = Counter(v.granularidad for v in valores).most_common(1)[0][0]
    puntos = sorted((v for v in valores if v.granularidad == granularidad), key=lambda v: v.fecha)
    inicio, fin = puntos[0], puntos[-1]

    if indicador.tipo == 'cualitativo':
        return {
            **base, 'sin_datos': False,
            'valor_inicio': inicio.valor_texto, 'valor_fin': fin.valor_texto,
            'variacion_abs': None, 'variacion_pct': None, 'promedio': None,
            'fecha_inicio': inicio.fecha, 'fecha_fin': fin.fecha, 'cantidad_puntos': len(puntos),
        }

    v_inicio, v_fin = inicio.valor_numerico, fin.valor_numerico
    numericos = [p.valor_numerico for p in puntos if p.valor_numerico is not None]
    promedio = (sum(numericos) / len(numericos)) if numericos else None
    variacion_abs = (v_fin - v_inicio) if (v_fin is not None and v_inicio is not None) else None
    # El % de variación solo tiene sentido con una base positiva: si el
    # valor inicial es negativo o cero (ej. resultado fiscal en déficit,
    # EMAE interanual negativo), dividir por él da un número que invierte
    # el signo de forma contraintuitiva (ej. de -1.8 a 0.3 "parece" una
    # baja de -116%). En esos casos se omite y queda solo la variación
    # absoluta, que sigue siendo válida.
    variacion_pct = (variacion_abs / v_inicio * 100) if (variacion_abs is not None and v_inicio and v_inicio > 0) else None

    return {
        **base, 'sin_datos': False,
        'valor_inicio': v_inicio, 'valor_fin': v_fin,
        'variacion_abs': variacion_abs, 'variacion_pct': variacion_pct, 'promedio': promedio,
        'fecha_inicio': inicio.fecha, 'fecha_fin': fin.fecha, 'cantidad_puntos': len(puntos),
    }


class GobiernoResumenView(APIView):
    """Resumen de todos los indicadores durante el período de un gobierno:
    valor al inicio del mandato, valor al final (o a hoy si sigue en
    curso), variación y promedio del período. Si un indicador no tiene
    ningún punto cargado dentro del rango (algo esperable para mandatos
    previos a la ventana de datos reales que tenemos), se informa
    `sin_datos: true` en vez de omitirlo, para que quede claro en la UI
    que falta esa serie histórica y no que el indicador no existe."""

    def get(self, request, gobierno_id):
        gobierno = get_object_or_404(Gobierno, id=gobierno_id)
        desde = gobierno.fecha_inicio
        hasta = gobierno.fecha_fin or date.today()

        indicadores = Indicador.objects.select_related('categoria', 'fuente').order_by('categoria__orden', 'orden')
        resumen = [_resumir_indicador(ind, desde, hasta) for ind in indicadores]

        return Response({
            'gobierno': GobiernoSerializer(gobierno).data,
            'desde': desde,
            'hasta': hasta,
            'indicadores': resumen,
        })


class PulsoIndexView(APIView):
    """El índice general (ver services/pulso_index.py): el score de la
    última foto guardada (con su tendencia contra la foto anterior — así
    se responde "¿el índice mismo está mejorando o empeorando?", no solo
    "¿cuántos indicadores mejoran hoy?"), el historial reciente para un
    sparkline, y el detalle en vivo (siempre recalculado, para que la
    lista de qué entra y en qué dirección nunca quede desactualizada
    aunque la foto guardada sea de otro día)."""

    def get(self, request):
        detalle_actual = pulso_index.calcular()
        snapshots = list(PulsoIndexSnapshot.objects.order_by('-fecha')[:30])

        if snapshots:
            actual = snapshots[0]
            anterior = snapshots[1] if len(snapshots) > 1 else None
            score, fecha = actual.score, actual.fecha
            mejorando, empeorando, sin_cambio, total = actual.mejorando, actual.empeorando, actual.sin_cambio, actual.total
            if anterior:
                diff = actual.score - anterior.score
                trend = 'up' if diff > 0 else ('down' if diff < 0 else 'flat')
                delta = diff
            else:
                trend = delta = None
            historial = [{'fecha': s.fecha, 'score': s.score} for s in reversed(snapshots)]
        else:
            # Todavía no se corrió compute_pulso_index para hoy: se
            # devuelve el cálculo en vivo, sin historial ni tendencia
            # propia (no hay una foto anterior con la que comparar).
            score, fecha = detalle_actual['score'], date.today()
            mejorando, empeorando, sin_cambio, total = (
                detalle_actual['mejorando'], detalle_actual['empeorando'],
                detalle_actual['sin_cambio'], detalle_actual['total'],
            )
            trend = delta = None
            historial = []

        return Response({
            'score': score, 'fecha': fecha, 'trend': trend, 'delta': delta,
            'mejorando': mejorando, 'empeorando': empeorando, 'sin_cambio': sin_cambio, 'total': total,
            'historial': historial,
            'detalle': detalle_actual['detalle'],
        })
