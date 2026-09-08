"""
El índice general: "¿el país está mejorando o empeorando, en conjunto?"
— respondido con DOS números, cada uno sobre una ventana de tiempo
distinta, en vez de uno solo:

1. **Últimos 30 días** (`calcular_ultimos_30_dias`): pulso de corto
   plazo — compara el valor de cada indicador al principio y al final de
   los últimos 30 días. Se recalcula y se guarda una foto por día (ver
   `compute_pulso_index`), así que tiene serie histórica propia.
2. **Mandato actual** (`calcular_mandato_actual`): compara el valor de
   cada indicador el día que asumió el gobierno en curso contra hoy —
   "¿este gobierno viene dejando el país mejor o peor de como lo
   encontró, hasta ahora?". Siempre se recalcula en vivo (es barato y
   nunca queda desactualizado); mientras el mandato siga en curso este
   número se sigue moviendo con cada dato nuevo, a diferencia del mismo
   cálculo ya cerrado para un gobierno anterior (ver
   `GobiernoResumenView`), que da un valor fijo.

Metodología de cada uno (a propósito simple y transparente, no una
fórmula opaca) — ver `services/resumen.py` para la implementación
compartida con la comparativa "Por gobierno":

1. Se toman solo los indicadores numéricos con `polaridad` definida
   ('positivo' o 'negativo') — ver Indicador.polaridad. Los que no tienen
   consenso amplio sobre qué dirección es una mejora (dólar, Merval, gasto
   militar, aprobación de gobierno, gasto público, canasta básica nominal)
   quedan afuera a propósito, no por descuido — meterlos obligaría a
   asumir una postura ideológica disfrazada de medición objetiva. Ver el
   comentario de POLARIDADES en seed_pulso_austral.py para el detalle de
   qué entra y por qué.
2. De cada uno se compara el valor al principio de la ventana contra el
   valor al final (mismo criterio que "Por gobierno": si hay puntos en
   más de una granularidad, se usa la más numerosa dentro del rango).
3. Se cuenta cuántos "mejoraron" (variación a favor de su polaridad),
   cuántos "empeoraron" (variación en contra) y cuántos quedaron "sin
   cambio".
4. El score es un índice de difusión: 50 + 50 × (mejoraron - empeoraron) / total.
   50 = tantos mejorando como empeorando. 100 = todos mejorando. 0 = todos
   empeorando. Es la misma lógica que un PMI o un "advance/decline" bursátil,
   no un promedio ponderado de unidades distintas (%, pb, US$ B...) que no
   se pueden sumar directamente sin normalizar de forma arbitraria.
"""

from __future__ import annotations

from datetime import date, timedelta

from indicadores.models import Gobierno, Indicador
from indicadores.services import resumen as resumen_svc

VENTANA_CORTO_PLAZO = timedelta(days=30)


def _detalle_desde_resumen(filas: list[dict]) -> list[dict]:
    """El detalle que ya mostraba el banner del índice: id/nombre/
    categoría/polaridad/dirección de cada indicador considerado (los que
    tienen `direccion` definida — ver resumen.resumir_indicador)."""
    return [
        {
            'id': r['id'], 'nombre': r['nombre'], 'categoria_id': r['categoria_id'],
            'polaridad': r['polaridad'], 'direccion': r['direccion'], 'fecha': r['fecha_fin'],
        }
        for r in filas
        if r.get('direccion') is not None
    ]


def calcular_ventana(desde: date, hasta: date) -> dict:
    """Índice general para una ventana [desde, hasta] arbitraria."""
    indicadores = Indicador.objects.select_related('categoria', 'fuente').order_by('categoria__orden', 'orden')
    filas = [resumen_svc.resumir_indicador(ind, desde, hasta) for ind in indicadores]
    agregado = resumen_svc.indice_general(filas)
    agregado['desde'] = desde
    agregado['hasta'] = hasta
    agregado['detalle'] = _detalle_desde_resumen(filas)
    return agregado


def calcular_ultimos_30_dias(hoy: date | None = None) -> dict:
    hoy = hoy or date.today()
    return calcular_ventana(hoy - VENTANA_CORTO_PLAZO, hoy)


def calcular_mandato_actual(hoy: date | None = None) -> dict | None:
    """None si no hay ningún gobierno cargado sin fecha_fin (no debería
    pasar en uso normal, pero evita un 500 si todavía no se cargó el
    gobierno en curso)."""
    hoy = hoy or date.today()
    actual = Gobierno.objects.filter(fecha_fin__isnull=True).order_by('-fecha_inicio').first()
    if not actual:
        return None
    resultado = calcular_ventana(actual.fecha_inicio, hoy)
    resultado['gobierno'] = {'id': actual.id, 'presidente': actual.presidente, 'fecha_inicio': actual.fecha_inicio}
    return resultado
