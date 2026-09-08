"""
Reemplaza los valores ilustrativos de un puñado de indicadores por datos
reales, tomados de fuentes públicas gratuitas y sin necesidad de API key:

- Dólar oficial y Reservas internacionales: serie diaria del BCRA
  (API "Estadísticas Monetarias" v4.0) — se derivan también las
  granularidades 'semana' y 'mes' resampleando esa misma serie diaria.
- Inflación interanual: serie mensual del BCRA (variable 28), con 'anio'
  derivado tomando el valor de diciembre (o el último mes cargado) de
  cada año.
- Dólar blue: solo el valor del día, vía dolarapi.com (mercado informal,
  el BCRA no lo publica).
- Merval: solo el valor del día, vía la API pública de BYMA (descubierta
  reverseando el cliente open-source `openbymadata` — ver
  `indicadores/services/bymadata.py`). No hay serie histórica pública
  para el índice (sí para acciones individuales, pero no es lo mismo),
  así que queda con el mismo patrón que dólar blue: un único punto 'dia'.
- EMAE y Desempleo: series de INDEC vía la API de datos.gob.ar (agrega
  datasets de varios organismos). El desempleo es trimestral en origen —
  se guarda igual bajo granularidad 'mes' (con la fecha de inicio del
  trimestre), mismo criterio que ya usábamos para datos de baja frecuencia.

Riesgo país queda pendiente: no encontramos una fuente pública gratuita y
sin autenticación — conectarlo significa contratar/registrar una API de
mercado (ver backend/README.md). Tampoco encontramos, en datos.gob.ar,
una serie nacional de pobreza/indigencia ni de canasta básica que
estuviera actualizada — quedan igual sin auto-actualizar por ahora (hay
puntos reales sueltos cargados a mano, ver seed_indicadores_reales.py).

Pensado para correrse periódicamente (cron / Celery beat) — es idempotente,
usa `bulk_create(update_conflicts=True)` (upsert vía ON CONFLICT DO UPDATE)
en vez de un `update_or_create` por punto, para no pagar 2 viajes de red
por cada uno de los ~900 puntos contra una base remota como Neon.

Uso:
    python manage.py fetch_datos_reales
"""

from __future__ import annotations

from datetime import date, timedelta

from django.core.management.base import BaseCommand

from indicadores.models import Indicador, IndicadorValor
from indicadores.services import bcra, bymadata, datos_gob_ar, dolarapi
from indicadores.services.bcra import BcraError
from indicadores.services.bymadata import BymaDataError
from indicadores.services.datos_gob_ar import DatosGobArError
from indicadores.services.dolarapi import DolarApiError

# Cubre todo el mandato de Milei (asumió 10-dic-2023) para que el "AL
# INICIO" de la comparativa por gobierno para dólar oficial y reservas
# salga solo del fetch real. Ojo: si la ventana empezara EL 10-dic o
# antes, esos días quedarían del lado de Alberto Fernández (su rango es
# inclusive hasta esa fecha) y la serie diaria real — con muchísimos más
# puntos que los pocos puntos sueltos que carga seed_indicadores_reales.py
# para gobiernos viejos — le "ganaría" el desempate de granularidad en
# _resumir_indicador, pisando su comparación con solo un puñado de días
# de su último mes en vez de todo su mandato. Por eso arranca 1 día
# después del límite (11-dic-2023): cero superposición con su rango.
VENTANA_DIARIA = timedelta(days=1000)

# IDs de series de datos.gob.ar ya resueltas a mano (búsquedas hechas contra
# https://apis.datos.gob.ar/series/api/search/?q=<texto>).
ID_EMAE_MENSUAL = '143.3_ICE_SERVIA_2004_A_25'   # "EMAE variacion interanual" — EMAE. Base 2004. Variación % interanual (mensual)
ID_EMAE_ANUAL = '143.1_ICE_SERVIA_2004_A_25'     # misma serie, versión anual
ID_DESEMPLEO_TRIMESTRAL = '42.3_EPH_PUNTUATAL_0_M_30'  # "tasa desocupacion total urbano nacional" — Tasa de desocupación total (trimestral)
ID_DESEMPLEO_ANUAL = '45.1_ECTDT_0_A_33'         # misma búsqueda — Tasa de desempleo total (anual)
ID_SALDO_COMERCIAL = '74.3_ISC_0_M_19'           # dataset "Intercambio Comercial Argentino" (INDEC) — Saldo comercial, mensual, US$ M
ID_EXPORTACIONES = '74.3_IET_0_M_16'             # mismo dataset — Exportaciones totales, mensual, US$ M


def _resamplear(serie_diaria: list[tuple[date, float]], clave):
    """Agrupa una serie diaria ascendente por `clave(fecha)` y se queda con
    el último valor de cada grupo (fin de semana ISO / fin de mes)."""
    agrupado: dict = {}
    for fecha, valor in serie_diaria:
        agrupado[clave(fecha)] = (fecha, valor)
    return sorted(agrupado.values())


def _fin_de_semana_iso(fecha: date):
    y, w, _ = fecha.isocalendar()
    return (y, w)


def _fin_de_mes(fecha: date):
    return (fecha.year, fecha.month)


def _con_deltas(serie: list[tuple[date, float]], sufijo: str, decimales: int = 1):
    """A partir de una serie [(fecha, valor), ...] devuelve una lista de
    dicts con delta_texto/trend calculados contra el punto anterior."""
    salida = []
    anterior = None
    for fecha, valor in serie:
        if anterior is None:
            delta_texto, trend = '', 'flat'
        else:
            diff = valor - anterior
            pct = (diff / anterior * 100) if anterior else 0
            trend = 'up' if diff > 0 else ('down' if diff < 0 else 'flat')
            delta_texto = f'{"+" if diff >= 0 else ""}{round(pct, decimales)}% {sufijo}'
        salida.append({'fecha': fecha, 'valor': valor, 'delta_texto': delta_texto, 'trend': trend})
        anterior = valor
    return salida


def _con_deltas_pp(serie: list[tuple[date, float]], sufijo: str, decimales: int = 1):
    """Como _con_deltas, pero para series cuyo valor ya es un porcentaje
    (EMAE, desempleo, inflación): el delta se expresa en puntos porcentuales
    (pp) — la diferencia absoluta, no el cambio relativo — porque un cambio
    relativo sobre un valor cercano a cero da números sin sentido (ej. EMAE
    pasando de 0.4% a 2.7% no es "+575%", son "+2.3pp")."""
    salida = []
    anterior = None
    for fecha, valor in serie:
        if anterior is None:
            delta_texto, trend = '', 'flat'
        else:
            diff = round(valor - anterior, decimales)
            trend = 'up' if diff > 0 else ('down' if diff < 0 else 'flat')
            delta_texto = f'{"+" if diff >= 0 else ""}{diff}pp {sufijo}'
        salida.append({'fecha': fecha, 'valor': valor, 'delta_texto': delta_texto, 'trend': trend})
        anterior = valor
    return salida


def _con_deltas_abs(serie: list[tuple[date, float]], sufijo: str, unidad_delta: str, decimales: int = 1):
    """Como _con_deltas_pp, pero para series que no son porcentajes (ej.
    saldo comercial en US$ M): el delta absoluto lleva la unidad propia del
    indicador en vez de "pp". Igual de necesario que _con_deltas_pp para
    valores que pueden cruzar el cero — el saldo comercial pasa de déficit a
    superávit y un % relativo ahí no tiene lectura sensata."""
    salida = []
    anterior = None
    for fecha, valor in serie:
        if anterior is None:
            delta_texto, trend = '', 'flat'
        else:
            diff = round(valor - anterior, decimales)
            if decimales == 0:
                diff = int(diff)  # evita el ".0" final que deja round() sobre un float
            trend = 'up' if diff > 0 else ('down' if diff < 0 else 'flat')
            delta_texto = f'{"+" if diff >= 0 else ""}{diff} {unidad_delta} {sufijo}'
        salida.append({'fecha': fecha, 'valor': valor, 'delta_texto': delta_texto, 'trend': trend})
        anterior = valor
    return salida


def _guardar_serie(indicador_id: str, granularidad: str, puntos: list[dict]):
    """Un solo bulk_create con upsert (ON CONFLICT DO UPDATE) en vez de un
    update_or_create por punto — con series de cientos de puntos contra una
    base remota (Neon), cada update_or_create es 2 viajes de red; esto lo
    manda todo en un puñado de consultas."""
    if not puntos:
        return 0
    objetos = [
        IndicadorValor(
            indicador_id=indicador_id, fecha=p['fecha'], granularidad=granularidad,
            valor_numerico=round(p['valor'], 4), delta_texto=p['delta_texto'], trend=p['trend'],
        )
        for p in puntos
    ]
    IndicadorValor.objects.bulk_create(
        objetos,
        update_conflicts=True,
        unique_fields=['indicador', 'fecha', 'granularidad'],
        update_fields=['valor_numerico', 'delta_texto', 'trend'],
        batch_size=500,
    )
    return len(objetos)


class Command(BaseCommand):
    help = 'Trae datos reales del BCRA y dolarapi.com para reemplazar los valores ilustrativos del seed.'

    # Los indicadores que este comando gestiona — se usa para marcar
    # Indicador.actualizacion_automatica=True al final, sin importar si el
    # fetch de ese día en particular tuvo éxito (el flag describe "esto lo
    # gestiona este comando", no "hoy se pudo actualizar"). Es la misma
    # lista que INDICADORES_CON_DATOS_REALES en seed_pulso_austral.py — se
    # marca desde los dos lados a propósito, para que agregar un indicador
    # nuevo acá sin recordar tocar el otro archivo no lo deje sin marcar.
    INDICADORES_GESTIONADOS = [
        'dolar_oficial', 'reservas_bcra', 'inflacion_interanual', 'dolar_blue', 'emae', 'desempleo',
        'balanza_comercial', 'exportaciones', 'merval',
    ]

    def handle(self, *args, **options):
        hoy = date.today()
        desde = hoy - VENTANA_DIARIA

        self._actualizar_serie_bcra(
            'dolar_oficial', bcra.ID_TIPO_CAMBIO_MINORISTA, desde, hoy, sufijo_dia='hoy', decimales=1,
        )
        self._actualizar_serie_bcra(
            'reservas_bcra', bcra.ID_RESERVAS_INTERNACIONALES, desde, hoy, sufijo_dia='en el día', decimales=1,
            transformar=lambda millones: millones / 1000,  # US$ M -> US$ B, unidad del indicador
        )
        self._actualizar_inflacion()
        self._actualizar_dolar_blue()
        self._actualizar_merval()
        self._actualizar_desde_datos_gob_ar(
            'emae', mensual_id=ID_EMAE_MENSUAL, anual_id=ID_EMAE_ANUAL, sufijo_mes='vs. mes anterior',
        )
        self._actualizar_desde_datos_gob_ar(
            'desempleo', mensual_id=ID_DESEMPLEO_TRIMESTRAL, anual_id=ID_DESEMPLEO_ANUAL, sufijo_mes='vs. trim. anterior',
        )
        self._actualizar_comercio_exterior()

        Indicador.objects.filter(id__in=self.INDICADORES_GESTIONADOS).update(actualizacion_automatica=True)

        self.stdout.write(self.style.SUCCESS('Listo.'))

    def _actualizar_serie_bcra(self, indicador_id, id_variable, desde, hasta, *, sufijo_dia, decimales, transformar=None):
        if not Indicador.objects.filter(id=indicador_id).exists():
            self.stdout.write(self.style.WARNING(f'{indicador_id}: no existe en la base, se salta (¿corriste el seed?).'))
            return
        try:
            serie = bcra.obtener_serie(id_variable, desde, hasta)
        except BcraError as exc:
            self.stdout.write(self.style.ERROR(f'{indicador_id}: {exc}'))
            return
        if not serie:
            self.stdout.write(self.style.WARNING(f'{indicador_id}: el BCRA no devolvió datos en el rango pedido.'))
            return
        if transformar:
            serie = [(f, transformar(v)) for f, v in serie]

        n_dia = _guardar_serie(indicador_id, 'dia', _con_deltas(serie, sufijo_dia, decimales))
        n_sem = _guardar_serie(indicador_id, 'semana', _con_deltas(_resamplear(serie, _fin_de_semana_iso), 'en la semana', decimales))
        n_mes = _guardar_serie(indicador_id, 'mes', _con_deltas(_resamplear(serie, _fin_de_mes), 'en el mes', decimales))

        # El BCRA suele publicar con 1-3 días hábiles de rezago: cualquier
        # punto posterior al último dato real solo puede ser un resabio del
        # seed ilustrativo (que insertaba un único valor "de hoy") — lo
        # borramos para que no tape el dato real más reciente.
        ultima_fecha_real = serie[-1][0]
        borrados = IndicadorValor.objects.filter(
            indicador_id=indicador_id, granularidad__in=['dia', 'semana', 'mes'], fecha__gt=ultima_fecha_real,
        ).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f'{indicador_id}: {n_dia} días, {n_sem} semanas, {n_mes} meses (BCRA, variable {id_variable})'
            + (f', {borrados} resabio(s) del seed borrados' if borrados else '') + '.'
        ))

    def _actualizar_inflacion(self):
        indicador_id = 'inflacion_interanual'
        if not Indicador.objects.filter(id=indicador_id).exists():
            self.stdout.write(self.style.WARNING(f'{indicador_id}: no existe en la base, se salta.'))
            return
        try:
            # Diez años de historia mensual para poblar también 'anio'.
            serie = bcra.obtener_serie(bcra.ID_INFLACION_INTERANUAL, date.today().replace(year=date.today().year - 10), date.today())
        except BcraError as exc:
            self.stdout.write(self.style.ERROR(f'{indicador_id}: {exc}'))
            return
        if not serie:
            self.stdout.write(self.style.WARNING(f'{indicador_id}: el BCRA no devolvió datos.'))
            return

        # Delta contra el mismo mes del año anterior (pp), como ya se
        # expresaba en el mock original ("-42pp vs. año anterior").
        por_fecha = dict(serie)
        puntos_mes = []
        for fecha, valor in serie:
            hace_un_anio = next((v for f, v in serie if f.year == fecha.year - 1 and f.month == fecha.month), None)
            if hace_un_anio is None:
                delta_texto, trend = '', 'flat'
            else:
                diff = round(valor - hace_un_anio, 1)
                trend = 'up' if diff > 0 else ('down' if diff < 0 else 'flat')
                delta_texto = f'{"+" if diff >= 0 else ""}{diff}pp vs. año anterior'
            puntos_mes.append({'fecha': fecha, 'valor': valor, 'delta_texto': delta_texto, 'trend': trend})
        n_mes = _guardar_serie(indicador_id, 'mes', puntos_mes)

        anual = _resamplear(serie, lambda f: f.year)  # último mes cargado de cada año (dic. normalmente)
        n_anio = _guardar_serie(indicador_id, 'anio', _con_deltas(anual, 'vs. año anterior', 1))

        # Mismo resabio posible que en _actualizar_serie_bcra: el seed
        # ilustrativo tenía puntos hasta el mes "actual" de la demo, pero el
        # BCRA publica inflación con varias semanas de rezago.
        ultima_fecha_real = serie[-1][0]
        borrados = IndicadorValor.objects.filter(
            indicador_id=indicador_id, granularidad__in=['mes', 'anio'], fecha__gt=ultima_fecha_real,
        ).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f'{indicador_id}: {n_mes} meses, {n_anio} años (BCRA, variable {bcra.ID_INFLACION_INTERANUAL})'
            + (f', {borrados} resabio(s) del seed borrados' if borrados else '') + '.'
        ))

    def _actualizar_dolar_blue(self):
        indicador_id = 'dolar_blue'
        if not Indicador.objects.filter(id=indicador_id).exists():
            self.stdout.write(self.style.WARNING(f'{indicador_id}: no existe en la base, se salta.'))
            return
        try:
            cotizaciones = dolarapi.obtener_cotizaciones()
        except DolarApiError as exc:
            self.stdout.write(self.style.ERROR(f'{indicador_id}: {exc}'))
            return
        blue = cotizaciones.get('blue')
        if not blue:
            self.stdout.write(self.style.WARNING(f'{indicador_id}: dolarapi.com no incluyó la casa "blue".'))
            return

        anterior = (
            IndicadorValor.objects.filter(indicador_id=indicador_id, granularidad='dia')
            .exclude(fecha=date.today())
            .order_by('-fecha')
            .first()
        )
        valor = float(blue['venta'])
        if anterior and anterior.valor_numerico:
            diff_pct = (valor - float(anterior.valor_numerico)) / float(anterior.valor_numerico) * 100
            trend = 'up' if diff_pct > 0 else ('down' if diff_pct < 0 else 'flat')
            delta_texto = f'{"+" if diff_pct >= 0 else ""}{round(diff_pct, 1)}% hoy'
        else:
            delta_texto, trend = '', 'flat'

        IndicadorValor.objects.update_or_create(
            indicador_id=indicador_id, fecha=date.today(), granularidad='dia',
            defaults={'valor_numerico': valor, 'delta_texto': delta_texto, 'trend': trend},
        )
        self.stdout.write(self.style.SUCCESS(f'{indicador_id}: ${valor} (dolarapi.com, casa "blue").'))

    def _actualizar_merval(self):
        indicador_id = 'merval'
        if not Indicador.objects.filter(id=indicador_id).exists():
            self.stdout.write(self.style.WARNING(f'{indicador_id}: no existe en la base, se salta.'))
            return
        try:
            merval = bymadata.obtener_merval()
        except BymaDataError as exc:
            self.stdout.write(self.style.ERROR(f'{indicador_id}: {exc}'))
            return

        # BYMA ya da la variación vs. el cierre anterior — se usa esa en vez
        # de recalcularla contra el último punto guardado, más autoritativa
        # (y evita depender de que ayer se haya corrido este comando).
        diff_pct = merval['variacion_pct']
        trend = 'up' if diff_pct > 0 else ('down' if diff_pct < 0 else 'flat')
        delta_texto = f'{"+" if diff_pct >= 0 else ""}{round(diff_pct, 1)}% hoy'

        IndicadorValor.objects.update_or_create(
            indicador_id=indicador_id, fecha=merval['fecha'], granularidad='dia',
            defaults={'valor_numerico': merval['valor'], 'delta_texto': delta_texto, 'trend': trend},
        )
        self.stdout.write(self.style.SUCCESS(f'{indicador_id}: {merval["valor"]} pts (BYMA, S&P MERVAL).'))

    def _actualizar_desde_datos_gob_ar(self, indicador_id, *, mensual_id, anual_id, sufijo_mes):
        """Genérico para series de datos.gob.ar con una variante de mayor
        frecuencia (mensual o trimestral, se guarda como 'mes') y una anual
        — mismo patrón que _actualizar_inflacion, reutilizado para EMAE y
        desempleo. Los valores de estas series vienen como fracción
        (0.078), por eso factor=100."""
        if not Indicador.objects.filter(id=indicador_id).exists():
            self.stdout.write(self.style.WARNING(f'{indicador_id}: no existe en la base, se salta.'))
            return
        try:
            serie_mes = datos_gob_ar.obtener_serie(mensual_id, ultimos_n=36, factor=100)
            serie_anio = datos_gob_ar.obtener_serie(anual_id, ultimos_n=10, factor=100)
        except DatosGobArError as exc:
            self.stdout.write(self.style.ERROR(f'{indicador_id}: {exc}'))
            return
        if not serie_mes:
            self.stdout.write(self.style.WARNING(f'{indicador_id}: datos.gob.ar no devolvió datos.'))
            return

        n_mes = _guardar_serie(indicador_id, 'mes', _con_deltas_pp(serie_mes, sufijo_mes))
        n_anio = _guardar_serie(indicador_id, 'anio', _con_deltas_pp(serie_anio, 'vs. año anterior')) if serie_anio else 0

        ultima_fecha_real = serie_mes[-1][0]
        borrados = IndicadorValor.objects.filter(
            indicador_id=indicador_id, granularidad__in=['mes', 'anio'], fecha__gt=ultima_fecha_real,
        ).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f'{indicador_id}: {n_mes} puntos, {n_anio} años (datos.gob.ar)'
            + (f', {borrados} resabio(s) del seed borrados' if borrados else '') + '.'
        ))

    def _actualizar_comercio_exterior(self):
        """Saldo comercial y exportaciones totales — dataset "Intercambio
        Comercial Argentino" (INDEC vía datos.gob.ar), ya en US$ M (mismo
        unidad que el indicador, sin necesidad de factor). No hay serie
        anual separada resuelta a mano para este dataset, así que 'anio' se
        arma resampleando la mensual (último mes cargado de cada año) —
        mismo criterio que ya usa _actualizar_inflacion."""
        self._actualizar_serie_comercio(
            'balanza_comercial', ID_SALDO_COMERCIAL,
            deltas=lambda serie, sufijo: _con_deltas_abs(serie, sufijo, 'US$ M', decimales=0),
        )
        self._actualizar_serie_comercio(
            'exportaciones', ID_EXPORTACIONES,
            deltas=_con_deltas,
        )

    def _actualizar_serie_comercio(self, indicador_id, serie_id, *, deltas):
        if not Indicador.objects.filter(id=indicador_id).exists():
            self.stdout.write(self.style.WARNING(f'{indicador_id}: no existe en la base, se salta.'))
            return
        try:
            serie = datos_gob_ar.obtener_serie(serie_id, ultimos_n=120)  # 10 años, para 'anio' vía resampleo
        except DatosGobArError as exc:
            self.stdout.write(self.style.ERROR(f'{indicador_id}: {exc}'))
            return
        if not serie:
            self.stdout.write(self.style.WARNING(f'{indicador_id}: datos.gob.ar no devolvió datos.'))
            return
        # La fuente trae más decimales de los que tienen sentido para una
        # cifra en millones de dólares (ej. 2193.8482095...) — se redondea
        # al millón, que es la precisión habitual con la que se reporta este
        # dato (mismo criterio que "US$ 29.400 M" en el mock original).
        serie = [(f, round(v)) for f, v in serie]

        n_mes = _guardar_serie(indicador_id, 'mes', deltas(serie, 'en el mes'))
        anual = _resamplear(serie, lambda f: f.year)
        n_anio = _guardar_serie(indicador_id, 'anio', deltas(anual, 'vs. año anterior'))

        ultima_fecha_real = serie[-1][0]
        borrados = IndicadorValor.objects.filter(
            indicador_id=indicador_id, granularidad__in=['mes', 'semana', 'dia', 'anio'], fecha__gt=ultima_fecha_real,
        ).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f'{indicador_id}: {n_mes} meses, {n_anio} años (datos.gob.ar, serie {serie_id})'
            + (f', {borrados} resabio(s) del seed borrados' if borrados else '') + '.'
        ))
