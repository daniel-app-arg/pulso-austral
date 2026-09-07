"""
Cliente de la API de series de tiempo de datos.gob.ar
(https://apis.datos.gob.ar/series/api/) — agrega en un solo lugar series de
INDEC, BCRA y otros organismos, sin necesidad de API key.

Cada serie tiene un `id` propio (se buscan por texto en `/search/`, ver
`fetch_datos_reales.py` para los que ya se resolvieron y quedaron
hardcodeados con un comentario del texto de búsqueda usado).
"""

from __future__ import annotations

from datetime import date, datetime

import requests

BASE_URL = 'https://apis.datos.gob.ar/series/api/series/'
TIMEOUT = 20


class DatosGobArError(Exception):
    pass


def obtener_serie(id_serie: str, *, ultimos_n: int = 60, factor: float = 1) -> list[tuple[date, float]]:
    """Últimos `ultimos_n` puntos de una serie, ascendente por fecha.
    `factor` multiplica el valor (varias series de INDEC vienen como
    fracción — 0.078 en vez de 7.8 — así que se pasa factor=100)."""
    try:
        resp = requests.get(BASE_URL, params={'ids': id_serie, 'limit': ultimos_n, 'sort': 'desc'}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise DatosGobArError(f'No se pudo conectar a datos.gob.ar (serie {id_serie}): {exc}') from exc

    if resp.status_code != 200:
        raise DatosGobArError(f'datos.gob.ar respondió {resp.status_code} para la serie {id_serie}: {resp.text[:200]}')

    puntos = resp.json().get('data') or []
    # La API devuelve fechas como "YYYY-MM-DD"; se normalizan por si vinieran con hora.
    salida = [(datetime.fromisoformat(f).date(), v * factor) for f, v in puntos]
    return sorted(salida)
