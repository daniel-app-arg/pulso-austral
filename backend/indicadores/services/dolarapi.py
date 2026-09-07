"""
Cliente de dolarapi.com — API pública y gratuita (sin key) con las
cotizaciones del día de distintos "dólares" argentinos. Se usa solo para el
dólar blue, que al ser un mercado informal no lo publica el BCRA; el dólar
oficial se toma directamente de la serie histórica del BCRA (ver bcra.py).
"""

from __future__ import annotations

import requests

BASE_URL = 'https://dolarapi.com/v1/dolares'
TIMEOUT = 15


class DolarApiError(Exception):
    pass


def obtener_cotizaciones() -> dict[str, dict]:
    """Devuelve las cotizaciones del día, indexadas por 'casa'
    ('oficial', 'blue', 'bolsa', 'mayorista', 'cripto', ...)."""
    try:
        resp = requests.get(BASE_URL, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise DolarApiError(f'No se pudo conectar a dolarapi.com: {exc}') from exc

    if resp.status_code != 200:
        raise DolarApiError(f'dolarapi.com respondió {resp.status_code}: {resp.text[:200]}')

    return {item['casa']: item for item in resp.json()}
