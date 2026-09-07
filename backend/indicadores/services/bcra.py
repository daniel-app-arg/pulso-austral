"""
Cliente de la API pública de "Estadísticas Monetarias" del BCRA (v4.0):
https://www.bcra.gob.ar/BCRAyVos/catalogo-de-datos-y-api.asp

No requiere API key. Nota sobre TLS: `curl` con el bundle de certificados de
Git Bash falla contra este host ("unable to get local issuer certificate")
porque ese bundle está desactualizado — no es un problema del certificado
del BCRA ni motivo para desactivar la verificación TLS. `requests` (que usa
`certifi`, más al día) valida la cadena sin problema; por eso este cliente
nunca pasa `verify=False`.
"""

from __future__ import annotations

from datetime import date, datetime

import requests

BASE_URL = 'https://api.bcra.gob.ar/estadisticas/v4.0/monetarias'
TIMEOUT = 20

# IDs de variable relevantes para Pulso Austral (ver catálogo completo en
# BASE_URL sin id: cada resultado trae {idVariable, descripcion, categoria}).
ID_RESERVAS_INTERNACIONALES = 1
ID_TIPO_CAMBIO_MINORISTA = 4
ID_INFLACION_MENSUAL = 27
ID_INFLACION_INTERANUAL = 28


class BcraError(Exception):
    pass


def obtener_serie(id_variable: int, desde: date, hasta: date) -> list[tuple[date, float]]:
    """Serie histórica (fecha, valor) de una variable, ordenada ascendente.
    Pagina automáticamente si el rango pedido supera el límite de la API."""
    puntos: dict[date, float] = {}
    offset = 0
    limit = 1000
    while True:
        try:
            resp = requests.get(
                f'{BASE_URL}/{id_variable}',
                params={'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'offset': offset, 'limit': limit},
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise BcraError(f'No se pudo conectar a la API del BCRA (variable {id_variable}): {exc}') from exc

        if resp.status_code != 200:
            raise BcraError(f'API del BCRA respondió {resp.status_code} para la variable {id_variable}: {resp.text[:200]}')

        data = resp.json()
        resultados = data.get('results') or []
        detalle = resultados[0]['detalle'] if resultados else []
        for punto in detalle:
            puntos[datetime.strptime(punto['fecha'], '%Y-%m-%d').date()] = float(punto['valor'])

        total = data.get('metadata', {}).get('resultset', {}).get('count', len(detalle))
        offset += limit
        if offset >= total or not detalle:
            break

    return sorted(puntos.items())
