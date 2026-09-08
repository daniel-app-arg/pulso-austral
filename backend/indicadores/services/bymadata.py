"""
Cliente de la API pública gratuita de BYMA (Bolsas y Mercados Argentinos),
sin necesidad de API key — descubierta a partir del cliente open-source
`openbymadata` (https://github.com/carvalab/openbymadata), que reversea el
endpoint que usa el propio sitio de BYMA para mostrar sus índices.

Solo expone el valor DEL DÍA (no hay endpoint público de serie histórica que
funcione para índices, a diferencia de las acciones individuales — se probó
`chart/historical-series/history` con el símbolo "M" y devuelve "no_data").
Por eso Merval queda con el mismo patrón que dólar blue en
fetch_datos_reales.py: un único punto 'dia', sin historias.
"""

from __future__ import annotations

import requests

BASE_URL = 'https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/index-price'
TIMEOUT = 15

SIMBOLO_MERVAL = 'M'


class BymaDataError(Exception):
    pass


def obtener_indices() -> dict[str, dict]:
    """Devuelve los índices de BYMA del día, indexados por símbolo
    ('M' = S&P MERVAL, 'G' = S&P BYMA Índice General, etc.)."""
    try:
        resp = requests.post(
            BASE_URL, timeout=TIMEOUT,
            headers={'Content-Type': 'application/json'},
            json={'Content-Type': 'application/json'},
        )
    except requests.RequestException as exc:
        raise BymaDataError(f'No se pudo conectar a BYMA: {exc}') from exc

    if resp.status_code != 200:
        raise BymaDataError(f'BYMA respondió {resp.status_code}: {resp.text[:200]}')

    data = resp.json().get('data') or []
    return {item['symbol']: item for item in data}


def obtener_merval() -> dict:
    """Último valor del índice S&P MERVAL: {'fecha', 'valor', 'variacion_pct'}."""
    indices = obtener_indices()
    merval = indices.get(SIMBOLO_MERVAL)
    if not merval:
        raise BymaDataError('BYMA no incluyó el símbolo "M" (S&P MERVAL) en la respuesta.')
    return {
        'fecha': merval['date'],
        'valor': float(merval['price']),
        'variacion_pct': float(merval['variation']) * 100,
    }
