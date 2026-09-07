"""
El índice general: "¿el país está mejorando o empeorando, en conjunto?"

Metodología (a propósito simple y transparente, no una fórmula opaca):

1. Se toman solo los indicadores numéricos con `polaridad` definida
   ('positivo' o 'negativo') — ver Indicador.polaridad. Los que no tienen
   consenso amplio sobre qué dirección es una mejora (dólar, Merval, gasto
   militar, aprobación de gobierno, gasto público, canasta básica nominal)
   quedan afuera a propósito, no por descuido — meterlos obligaría a
   asumir una postura ideológica disfrazada de medición objetiva. Ver el
   comentario de POLARIDADES en seed_pulso_austral.py para el detalle de
   qué entra y por qué.
2. De cada uno se mira el `trend` (up/down/flat) de su último valor
   cargado — el mismo dato que ya se muestra en su tarjeta del dashboard,
   no un cálculo nuevo.
3. Se cuenta cuántos "mejoraron" (trend a favor de su polaridad), cuántos
   "empeoraron" (trend en contra) y cuántos quedaron "sin cambio" (flat).
4. El score es un índice de difusión: 50 + 50 × (mejoraron - empeoraron) / total.
   50 = tantos mejorando como empeorando. 100 = todos mejorando. 0 = todos
   empeorando. Es la misma lógica que un PMI o un "advance/decline" bursátil,
   no un promedio ponderado de unidades distintas (%, pb, US$ B...) que no
   se pueden sumar directamente sin normalizar de forma arbitraria.

Esto es una fotografía de "hacia dónde apunta cada indicador ahora", no un
promedio de niveles — un país puede tener indicadores en niveles todavía
malos pero todos mejorando (score alto) o en niveles buenos pero todos
empeorando (score bajo). Ambas cosas son información real.
"""

from __future__ import annotations

from django.db.models import Case, IntegerField, When

from indicadores.models import Indicador, IndicadorValor

# Cuando un indicador tiene dos puntos con la MISMA fecha en granularidades
# distintas (pasa seguido: la granularidad 'anio'/'mes' de un resample toma
# "el último dato disponible ese período", que a mitad de año cae el mismo
# día que el último punto 'mes'/'dia'), hace falta un desempate explícito
# — sin esto, el orden que devuelve la fila empatada no está garantizado
# por SQL y puede cambiar entre consultas. Mismo criterio de precedencia
# que ya usa el frontend para elegir qué delta mostrar en la tarjeta
# (mes > año > semana > día): así el índice general nunca "mira" un dato
# distinto del que el usuario ya ve en la tarjeta de ese indicador.
_PRIORIDAD_GRANULARIDAD = Case(
    When(granularidad='mes', then=0),
    When(granularidad='anio', then=1),
    When(granularidad='semana', then=2),
    When(granularidad='dia', then=3),
    default=4,
    output_field=IntegerField(),
)


def calcular() -> dict:
    indicadores = list(
        Indicador.objects.filter(tipo='numerico', polaridad__in=['positivo', 'negativo'])
        .select_related('categoria')
    )

    # Una sola consulta para el último valor de TODOS los indicadores, no
    # una por indicador — contra una base remota como Neon, 31 queries
    # separadas (una por cada `.filter(indicador=ind).first()`) son 31
    # round-trips; ordenando por indicador, fecha descendente y prioridad
    # de granularidad, el primer registro de cada indicador ya es el que
    # corresponde.
    ids = [ind.id for ind in indicadores]
    ultimo_por_indicador = {}
    valores = (
        IndicadorValor.objects.filter(indicador_id__in=ids)
        .annotate(_prioridad=_PRIORIDAD_GRANULARIDAD)
        .order_by('indicador_id', '-fecha', '_prioridad')
    )
    for v in valores:
        ultimo_por_indicador.setdefault(v.indicador_id, v)

    mejorando = empeorando = sin_cambio = 0
    detalle = []

    for ind in indicadores:
        ultimo = ultimo_por_indicador.get(ind.id)
        if not ultimo or not ultimo.trend:
            continue

        if ultimo.trend == 'flat':
            direccion = 'sin_cambio'
            sin_cambio += 1
        else:
            mejora = (ultimo.trend == 'up') == (ind.polaridad == 'positivo')
            if mejora:
                direccion = 'mejora'
                mejorando += 1
            else:
                direccion = 'empeora'
                empeorando += 1

        detalle.append({
            'id': ind.id,
            'nombre': ind.nombre,
            'categoria_id': ind.categoria_id,
            'polaridad': ind.polaridad,
            'trend': ultimo.trend,
            'direccion': direccion,
            'fecha': ultimo.fecha,
        })

    total = mejorando + empeorando + sin_cambio
    score = 50 + 50 * (mejorando - empeorando) / total if total else 50.0

    return {
        'score': round(score, 1),
        'mejorando': mejorando,
        'empeorando': empeorando,
        'sin_cambio': sin_cambio,
        'total': total,
        'detalle': detalle,
    }
