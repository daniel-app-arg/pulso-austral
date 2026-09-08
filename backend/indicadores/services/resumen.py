"""
Resume indicadores dentro de un rango de fechas arbitrario — valor al
inicio y al final del rango, variación, y si esa variación es una
"mejora" o un "empeoramiento" según la polaridad de cada indicador.

Es el mecanismo que comparten dos features distintas que en el fondo son
la misma pregunta con distinto rango de fechas:

- GobiernoResumenView (views.py): rango = [fecha_inicio, fecha_fin] de un
  gobierno — "¿cómo cerró esta gestión?"
- PulsoIndexView, vía services/pulso_index.py: rango = últimos 30 días, o
  [fecha_inicio del mandato actual, hoy] — "¿el país está mejorando en lo
  reciente? ¿y desde que arrancó este gobierno?"

Antes vivía duplicado/hardcodeado en cada lugar; se separó acá para que
las tres vistas usen exactamente el mismo criterio de desempate de
granularidad y de exclusión de indicadores sin polaridad definida.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from indicadores.models import Indicador, IndicadorValor


def resumir_indicador(indicador: Indicador, desde: date, hasta: date) -> dict:
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
            'direccion': None,
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

    # Solo los indicadores con polaridad definida entran en "mejora" o
    # "empeora" — dólar, Merval, gasto militar, etc. quedan afuera del
    # cómputo agregado (no hay consenso sobre qué dirección es "mejor"),
    # aunque igual se muestran en la tabla con su variación cruda.
    direccion = None
    if variacion_abs is not None and indicador.polaridad in ('positivo', 'negativo'):
        if variacion_abs == 0:
            direccion = 'sin_cambio'
        else:
            mejora = (variacion_abs > 0) == (indicador.polaridad == 'positivo')
            direccion = 'mejora' if mejora else 'empeora'

    return {
        **base, 'sin_datos': False,
        'valor_inicio': v_inicio, 'valor_fin': v_fin,
        'variacion_abs': variacion_abs, 'variacion_pct': variacion_pct, 'promedio': promedio,
        'fecha_inicio': inicio.fecha, 'fecha_fin': fin.fecha, 'cantidad_puntos': len(puntos),
        'direccion': direccion,
    }


def indice_general(resumen: list[dict]) -> dict:
    """Índice de difusión sobre un resumen ya calculado (ver
    resumir_indicador): score = 50 + 50×(mejora-empeora)/total. 50 es
    tantos mejorando como empeorando, 100 es todos mejorando, 0 es todos
    empeorando — misma lógica que un PMI o un "advance/decline" bursátil."""
    mejorando = sum(1 for r in resumen if r.get('direccion') == 'mejora')
    empeorando = sum(1 for r in resumen if r.get('direccion') == 'empeora')
    sin_cambio = sum(1 for r in resumen if r.get('direccion') == 'sin_cambio')
    total = mejorando + empeorando + sin_cambio
    score = 50 + 50 * (mejorando - empeorando) / total if total else None
    return {
        'score': round(score, 1) if score is not None else None,
        'mejorando': mejorando, 'empeorando': empeorando, 'sin_cambio': sin_cambio, 'total': total,
    }


def resumen_rango(desde: date, hasta: date) -> dict:
    """Resume TODOS los indicadores + el índice general agregado, para un
    rango de fechas arbitrario."""
    indicadores = Indicador.objects.select_related('categoria', 'fuente').order_by('categoria__orden', 'orden')
    resumen = [resumir_indicador(ind, desde, hasta) for ind in indicadores]
    return {
        'desde': desde, 'hasta': hasta,
        'indice_general': indice_general(resumen),
        'indicadores': resumen,
    }
