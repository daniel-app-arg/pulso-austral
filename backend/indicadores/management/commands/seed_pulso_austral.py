"""
Comando de seed: carga las categorías, fuentes e indicadores del esquema SQL
original (pulso-austral-schema.sql) más las series mensuales/anuales que ya
estaban a mano en el mock del artifact (pulso-austral.jsx), para tener datos
de desarrollo realistas sin depender de Supabase.

Nota: solo se cargan granularidades 'mes' y 'anio' (las que estaban escritas
a mano en el mock). Las series diarias/semanales del artifact eran generadas
sintéticamente con ruido aleatorio en el frontend — no vale la pena portarlas
1:1; quedan como pendiente para cuando se conecte una fuente real (BCRA/INDEC
sí publican series diarias/semanales para varios de estos indicadores).

Uso:
    python manage.py seed_pulso_austral
    python manage.py seed_pulso_austral --flush   (borra todo antes de cargar)

⚠️ Ojo con el orden: este comando sobreescribe TODOS los indicadores del
mock (dolar_oficial, dolar_blue, reservas_bcra, inflacion_interanual, emae,
desempleo incluidos) con sus valores ilustrativos originales — pisa
cualquier dato real que haya cargado `fetch_datos_reales`. Si ya corriste
ese comando, volvé a correrlo después de este para restaurar los valores
reales:
    python manage.py seed_pulso_austral
    python manage.py fetch_datos_reales
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from indicadores.models import Categoria, EventoTimeline, Fuente, Indicador, IndicadorValor, Noticia

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def periodos_mensuales(n, fin=date(2026, 9, 1)):
    """Los últimos n primeros-de-mes, terminando en `fin` (inclusive)."""
    out = []
    for i in range(n - 1, -1, -1):
        mes = fin.month - i
        anio = fin.year
        while mes <= 0:
            mes += 12
            anio -= 1
        out.append(date(anio, mes, 1))
    return out


def anios_1_de_enero(n, fin_anio=2026):
    return [date(fin_anio - i, 1, 1) for i in range(n - 1, -1, -1)]


PERIODOS_14M = periodos_mensuales(14)
ANIOS_10 = anios_1_de_enero(10)

CATEGORIAS = [
    ("macro", "Macroeconomía", "#C98A2C", "Landmark", 1),
    ("empleo", "Empleo y trabajo", "#1F6F6B", "Users", 2),
    ("pobreza", "Pobreza y desigualdad", "#A23B2E", "Scale", 3),
    ("produccion", "Producción y actividad", "#7A6A3F", "Factory", 4),
    ("sector_externo", "Sector externo y financiero", "#2C6E8E", "TrendingUp", 5),
    ("institucional", "Institucional y gobernanza", "#5B4B8A", "Landmark", 6),
    ("bienestar", "Bienestar social", "#3E7C4A", "HeartPulse", 7),
    ("percepcion", "Percepción y sentimiento", "#8A5A3F", "Gauge", 8),
    ("geo", "Geopolítica", "#A23B2E", "Globe2", 9),
    ("seguridad", "Seguridad", "#7A2E3B", "Shield", 10),
    ("desarrollo_militar", "Desarrollo militar", "#4B5320", "Swords", 11),
]

FUENTES = [
    ("INDEC", "https://www.indec.gob.ar/"),
    ("BCRA", "https://www.bcra.gob.ar/"),
    ("Ámbito Financiero", "https://www.ambito.com/contenidos/riesgo-pais.html"),
    ("Ministerio de Economía", "https://www.argentina.gob.ar/economia"),
    ("FMI", "https://www.imf.org/en/Countries/ARG"),
    ("S&P Global Ratings", "https://www.spglobal.com/ratings/en/"),
    ("Mercosur", "https://www.mercosur.int/"),
    ("Bolsa de Comercio de Rosario", "https://www.bcr.com.ar/"),
    ("Transparencia Internacional", "https://www.transparency.org/en/countries/argentina"),
    ("World Justice Project", "https://worldjusticeproject.org/"),
    ("Universidad Torcuato Di Tella", "https://www.utdt.edu/"),
    ("Ministerio de Salud", "https://www.argentina.gob.ar/salud"),
    ("Management & Fit", "https://www.mmayfit.com/"),
    ("Ministerio de Seguridad", "https://www.argentina.gob.ar/seguridad"),
    ("SNEEP - Ministerio de Justicia", "https://www.argentina.gob.ar/justicia/politicacriminal/estadisticas/sneep"),
    ("Observatorio de la Deuda Social Argentina (UCA)", "https://uca.edu.ar/es/observatorio-de-la-deuda-social-argentina"),
    ("Ministerio de Defensa", "https://www.argentina.gob.ar/defensa"),
    ("SIPRI", "https://www.sipri.org/databases/milex"),
    ("Global Firepower", "https://www.globalfirepower.com/country-military-strength-detail.php?country_id=argentina"),
]

# Indicadores que fetch_datos_reales.py reemplaza con datos reales de una
# fuente externa (BCRA, datos.gob.ar, dolarapi.com) — todo lo que no está
# en este set se considera ilustrativo. Es la fuente de verdad de
# Indicador.actualizacion_automatica (ver defaults más abajo): declararlo
# acá, en vez de dejar que fetch_datos_reales.py lo marque por su cuenta,
# evita que rehacer este seed (que reescribe TODOS los indicadores) borre
# la marca sin querer — mismo tipo de bug que ya pasó una vez con los
# valores de IndicadorValor.
INDICADORES_CON_DATOS_REALES = {
    'dolar_oficial', 'dolar_blue', 'reservas_bcra', 'inflacion_interanual', 'emae', 'desempleo',
}

# Polaridad de cada indicador para el índice general (ver
# indicadores/services/pulso_index.py): 'positivo' si subir es mejorar,
# 'negativo' si subir es empeorar. Todo lo que NO está en este dict queda
# en 'neutral' (default del modelo) — es decir, afuera del índice — y es
# una exclusión deliberada, no un olvido:
#   - dolar_oficial, dolar_blue, merval: instrumentales/contestados — no
#     hay consenso sobre si un dólar más alto o más bajo es "mejor".
#   - gasto_defensa, efectivos_ffaa, inversion_equipamiento,
#     ranking_poder_militar: si más poder militar es deseable depende de
#     postura política, no es un hecho económico/social como los demás.
#   - aprobacion_gobierno, confianza_gobierno: son sobre qué tan popular
#     es el gobierno de turno, no sobre el estado del país — meterlos
#     haría que el índice premie a un gobierno por ser querido, no por
#     mejorar indicadores reales.
#   - gasto_publico: subir o bajar el gasto público es una discusión
#     ideológica (más Estado vs. menos Estado), no tiene una dirección
#     "mejor" consensuada.
#   - canasta_basica: está en pesos nominales, así que con inflación alta
#     SIEMPRE sube — no es una señal útil de mejora/empeoramiento por sí
#     sola (para eso ya está salario_real, que sí es comparable).
#   - tasa_encarcelamiento: más gente presa puede leerse como "el sistema
#     persigue mejor el delito" o como "sobrepoblación carcelaria" —
#     ambiguo, sin dirección de consenso.
#   - los 4 indicadores cualitativos de geo (valor_texto, no numérico) ya
#     quedan afuera solo por tipo, sin necesito declararlos acá.
POLARIDADES = {
    # macro
    'inflacion_interanual': 'negativo',
    'riesgo_pais': 'negativo',
    'reservas_bcra': 'positivo',
    'resultado_fiscal': 'positivo',
    # empleo
    'desempleo': 'negativo',
    'salario_real': 'positivo',
    'empleo_informal': 'negativo',
    # pobreza
    'tasa_pobreza': 'negativo',
    'tasa_indigencia': 'negativo',
    'gini': 'negativo',
    'brecha_ingresos': 'negativo',
    # produccion
    'emae': 'positivo',
    'ipi_manufacturero': 'positivo',
    'capacidad_instalada': 'positivo',
    'produccion_agropecuaria': 'positivo',
    # sector_externo
    'balanza_comercial': 'positivo',
    'cuenta_corriente': 'positivo',
    'deuda_externa': 'negativo',
    'exportaciones': 'positivo',
    # institucional
    'cpi_corrupcion': 'positivo',
    'estado_derecho': 'positivo',
    # bienestar
    'esperanza_vida': 'positivo',
    'cobertura_salud': 'positivo',
    'mortalidad_infantil': 'negativo',
    'acceso_servicios': 'positivo',
    # percepcion
    'confianza_consumidor': 'positivo',
    'expectativas_inflacion': 'negativo',
    'humor_social': 'positivo',
    # seguridad
    'tasa_homicidios': 'negativo',
    'delitos_propiedad': 'negativo',
    'percepcion_inseguridad': 'negativo',
}

# (id, categoria, nombre, tipo, unidad, destacado, fuente_nombre, orden,
#  valores_mensuales[14] | None, valores_anuales[10] | None,
#  valor_actual_si_no_tiene_historias, delta_texto, trend)
INDICADORES = [
    (
        "dolar_oficial", "macro", "Dólar oficial", "numerico", "$", True, "BCRA", 0,
        None, None, 1042, "+0.4% hoy", "up",
    ),
    (
        "dolar_blue", "macro", "Dólar blue", "numerico", "$", True, "BCRA", 0,
        None, None, 1380, "-0.7% hoy", "down",
    ),
    (
        "merval", "macro", "Merval", "numerico", "pts", True, "Ámbito Financiero", 0,
        None, None, 1852340, "+1.8% hoy", "up",
    ),
    (
        "inflacion_interanual", "macro", "Inflación interanual", "numerico", "%", False, "INDEC", 1,
        [268, 245, 225, 205, 188, 172, 158, 146, 136, 128, 122, 120, 119, 118],
        [25, 48, 54, 36, 51, 95, 140, 190, 230, 118],
        None, "-42pp vs. año anterior", "down",
    ),
    (
        "riesgo_pais", "macro", "Riesgo país (EMBI)", "numerico", "pb", False, "Ámbito Financiero", 2,
        [950, 910, 880, 850, 820, 790, 760, 730, 700, 670, 650, 635, 620, 612],
        [450, 550, 800, 1500, 1700, 2000, 1900, 1600, 900, 612],
        None, "-38pb en el mes", "down",
    ),
    (
        "reservas_bcra", "macro", "Reservas netas BCRA", "numerico", "US$ B", False, "BCRA", 3,
        [18.0, 18.5, 19.2, 20.0, 20.8, 21.5, 22.3, 23.1, 24.0, 24.9, 25.8, 27.0, 28.2, 29.4],
        [10, 8, 5, 3, -3, -5, 2, 10, 18, 29.4],
        None, "+US$1.200M en el mes", "up",
    ),
    (
        "resultado_fiscal", "macro", "Resultado fiscal primario", "numerico", "% PBI", False, "Ministerio de Economía", 4,
        [-1.8, -1.5, -1.3, -1.0, -0.8, -0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.15, 0.25, 0.3],
        [-4.2, -3.8, -3.5, -6.5, -3.0, -2.4, -1.5, -0.5, -0.2, 0.3],
        None, "superávit 8vo mes", "up",
    ),
    (
        "desempleo", "empleo", "Desempleo", "numerico", "%", False, "INDEC", 1,
        [6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, 7.0, 7.1, 7.2],
        [8.3, 9.1, 9.8, 11.5, 8.7, 7.1, 6.2, 6.9, 7.5, 7.2],
        None, "+0.3pp vs. trim. anterior", "up",
    ),
    (
        "salario_real", "empleo", "Salario real", "numerico", "%", False, "INDEC", 2,
        [-6.5, -6.0, -5.5, -5.0, -4.5, -4.0, -3.5, -3.0, -2.6, -2.2, -1.9, -1.7, -1.6, -1.4],
        [3.0, -2.0, -5.7, -2.5, 4.0, -3.0, -12.0, -8.0, -4.0, -1.4],
        None, "interanual", "down",
    ),
    (
        "empleo_informal", "empleo", "Empleo informal", "numerico", "%", False, "INDEC", 3,
        [42.5, 42.3, 42.1, 42.0, 41.9, 42.0, 41.9, 41.8, 41.9, 41.8, 41.9, 41.8, 41.9, 41.8],
        [33.5, 34.0, 35.1, 36.8, 36.0, 35.5, 38.0, 40.5, 42.0, 41.8],
        None, "sin cambios", "flat",
    ),
    (
        "canasta_basica", "empleo", "Canasta básica total", "numerico", "$", False, "INDEC", 4,
        [850000, 880000, 910000, 940000, 970000, 1000000, 1030000, 1060000, 1080000, 1100000, 1115000, 1130000, 1140000, 1150000],
        [18000, 25000, 38000, 55000, 95000, 190000, 420000, 750000, 980000, 1150000],
        None, "familia tipo, +2.1% mensual", "up",
    ),
    # -- pobreza -----------------------------------------------------------
    (
        "tasa_pobreza", "pobreza", "Tasa de pobreza", "numerico", "%", False, "INDEC", 1,
        [38.1, 37.6, 37.0, 36.5, 36.0, 35.5, 35.0, 34.6, 34.2, 33.9, 33.6, 33.4, 33.2, 33.0],
        [25.7, 32.0, 35.5, 42.0, 37.3, 39.2, 41.7, 52.9, 38.1, 33.0],
        None, "-5.1pp interanual", "down",
    ),
    (
        "tasa_indigencia", "pobreza", "Tasa de indigencia", "numerico", "%", False, "INDEC", 2,
        [9.5, 9.3, 9.1, 9.0, 8.9, 8.8, 8.7, 8.6, 8.5, 8.4, 8.3, 8.2, 8.1, 8.0],
        [4.8, 6.7, 8.0, 10.5, 8.2, 8.1, 11.9, 18.1, 9.5, 8.0],
        None, "-1.5pp interanual", "down",
    ),
    (
        "gini", "pobreza", "Coeficiente de Gini", "numerico", "índice", False, "INDEC", 3,
        [0.438, 0.437, 0.436, 0.436, 0.435, 0.434, 0.434, 0.433, 0.432, 0.432, 0.431, 0.431, 0.430, 0.430],
        [0.429, 0.441, 0.447, 0.452, 0.447, 0.439, 0.435, 0.448, 0.438, 0.430],
        None, "-0.008 interanual", "down",
    ),
    (
        "brecha_ingresos", "pobreza", "Brecha de ingresos (decil 10/decil 1)", "numerico", "veces", False, "INDEC", 4,
        [19.0, 18.8, 18.7, 18.6, 18.5, 18.4, 18.3, 18.2, 18.1, 18.0, 17.9, 17.9, 17.8, 17.8],
        [16.9, 18.0, 19.5, 21.0, 19.0, 18.2, 18.8, 21.5, 19.0, 17.8],
        None, "-1.2 veces interanual", "down",
    ),
    # -- produccion ----------------------------------------------------------
    (
        "emae", "produccion", "EMAE (actividad económica)", "numerico", "%", False, "INDEC", 1,
        [3.2, 3.4, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.5, 4.6],
        [2.7, -2.6, -2.1, -9.9, 10.4, 5.2, -1.6, -3.4, 3.8, 4.6],
        None, "+0.1pp vs. mes anterior", "up",
    ),
    (
        "ipi_manufacturero", "produccion", "Producción industrial (IPI)", "numerico", "%", False, "INDEC", 2,
        [0.5, 0.9, 1.2, 1.5, 1.8, 2.0, 2.3, 2.6, 2.8, 3.0, 3.2, 3.3, 3.4, 3.5],
        [-0.1, -4.6, -6.6, -7.6, 16.4, 3.9, -3.3, -9.8, 2.1, 3.5],
        None, "+0.1pp vs. mes anterior", "up",
    ),
    (
        "capacidad_instalada", "produccion", "Utilización de capacidad instalada", "numerico", "%", False, "INDEC", 3,
        [60.8, 61.0, 61.3, 61.5, 61.8, 62.0, 62.3, 62.6, 62.8, 63.0, 63.2, 63.3, 63.4, 63.5],
        [65.7, 63.4, 59.4, 56.6, 63.2, 65.0, 61.6, 57.2, 60.8, 63.5],
        None, "+0.1pp vs. mes anterior", "up",
    ),
    (
        "produccion_agropecuaria", "produccion", "Producción agropecuaria (cosecha gruesa)", "numerico", "Mt", False, "Bolsa de Comercio de Rosario", 4,
        [131.0, 131.3, 131.6, 131.9, 132.2, 132.5, 132.8, 133.1, 133.4, 133.7, 134.0, 134.2, 134.3, 134.5],
        [108.4, 88.6, 141.4, 140.1, 128.8, 96.9, 100.6, 125.6, 131.0, 134.5],
        None, "+3.5Mt vs. campaña anterior", "up",
    ),
    # -- sector_externo ------------------------------------------------------
    (
        "balanza_comercial", "sector_externo", "Balanza comercial", "numerico", "US$ M", False, "INDEC", 1,
        [1100, 1140, 1180, 1210, 1240, 1260, 1290, 1310, 1330, 1350, 1370, 1390, 1410, 1430],
        [-3417, -3820, 15914, 12507, 14750, 6923, -6923, 18762, 15200, 16800],
        None, "+US$20M vs. mes anterior", "up",
    ),
    (
        "cuenta_corriente", "sector_externo", "Cuenta corriente", "numerico", "% PBI", False, "BCRA", 2,
        [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.5],
        [-4.8, -5.2, -0.8, 0.9, 1.4, -0.2, -3.2, -1.0, 0.8, 1.5],
        None, "+0.1pp vs. trim. anterior", "up",
    ),
    (
        "deuda_externa", "sector_externo", "Deuda externa bruta", "numerico", "US$ B", False, "BCRA", 3,
        [285.0, 284.4, 283.8, 283.2, 282.6, 282.0, 281.4, 280.9, 280.4, 279.9, 279.5, 279.2, 279.1, 279.0],
        [234.0, 277.9, 277.7, 271.8, 274.8, 276.8, 289.4, 293.4, 285.0, 279.0],
        None, "-US$0.1B en el mes", "down",
    ),
    (
        "exportaciones", "sector_externo", "Exportaciones", "numerico", "US$ M", False, "INDEC", 4,
        [6900, 6950, 7000, 7050, 7100, 7150, 7200, 7300, 7400, 7500, 7600, 7700, 7750, 7800],
        [5200, 5400, 5100, 4600, 6800, 7300, 6100, 6900, 7400, 7800],
        None, "+US$50M vs. mes anterior", "up",
    ),
    # -- institucional --------------------------------------------------------
    (
        "cpi_corrupcion", "institucional", "Índice de percepción de la corrupción", "numerico", "puntos", False, "Transparencia Internacional", 1,
        [39.0, 39.2, 39.3, 39.5, 39.6, 39.8, 39.9, 40.1, 40.2, 40.4, 40.5, 40.7, 40.8, 41.0],
        [39, 40, 45, 42, 38, 38, 37, 37, 39, 41],
        None, "+2 puntos interanual", "up",
    ),
    (
        "estado_derecho", "institucional", "Índice de estado de derecho", "numerico", "índice", False, "World Justice Project", 2,
        [0.505, 0.506, 0.507, 0.508, 0.509, 0.510, 0.511, 0.512, 0.513, 0.514, 0.515, 0.516, 0.518, 0.520],
        [0.52, 0.51, 0.50, 0.49, 0.48, 0.49, 0.50, 0.50, 0.51, 0.52],
        None, "+0.005 interanual", "up",
    ),
    (
        "gasto_publico", "institucional", "Gasto público consolidado", "numerico", "% PBI", False, "Ministerio de Economía", 3,
        [33.0, 32.9, 32.8, 32.7, 32.6, 32.5, 32.4, 32.3, 32.2, 32.2, 32.1, 32.1, 32.0, 32.0],
        [42.1, 40.6, 39.7, 45.6, 40.5, 38.9, 39.8, 33.5, 32.8, 32.0],
        None, "-0.8pp interanual", "down",
    ),
    (
        "confianza_gobierno", "institucional", "Confianza en el gobierno", "numerico", "puntos", False, "Universidad Torcuato Di Tella", 4,
        [2.6, 2.6, 2.58, 2.57, 2.56, 2.55, 2.54, 2.53, 2.52, 2.51, 2.50, 2.50, 2.51, 2.5],
        [2.3, 1.6, 1.3, 2.1, 1.5, 1.2, 1.6, 2.4, 2.6, 2.5],
        None, "-0.1pt en el mes", "down",
    ),
    # -- bienestar -------------------------------------------------------------
    (
        "esperanza_vida", "bienestar", "Esperanza de vida al nacer", "numerico", "años", False, "INDEC", 1,
        [77.1, 77.1, 77.1, 77.15, 77.15, 77.2, 77.2, 77.2, 77.25, 77.25, 77.25, 77.3, 77.3, 77.3],
        [76.7, 76.8, 76.9, 76.0, 75.5, 76.3, 76.8, 77.0, 77.2, 77.3],
        None, "+0.1 años interanual", "up",
    ),
    (
        "cobertura_salud", "bienestar", "Cobertura de salud", "numerico", "%", False, "INDEC", 2,
        [65.5, 65.6, 65.7, 65.8, 65.9, 66.0, 66.0, 66.1, 66.2, 66.3, 66.3, 66.4, 66.4, 66.5],
        [63.8, 64.5, 64.0, 63.0, 62.5, 63.5, 64.2, 65.0, 65.8, 66.5],
        None, "+0.7pp interanual", "up",
    ),
    (
        "mortalidad_infantil", "bienestar", "Tasa de mortalidad infantil", "numerico", "por mil", False, "Ministerio de Salud", 3,
        [7.6, 7.58, 7.55, 7.53, 7.5, 7.48, 7.45, 7.42, 7.4, 7.38, 7.35, 7.33, 7.31, 7.3],
        [9.7, 9.4, 9.0, 8.7, 8.4, 8.6, 8.2, 7.9, 7.6, 7.3],
        None, "-0.3pp interanual", "down",
    ),
    (
        "acceso_servicios", "bienestar", "Acceso a servicios básicos (agua y cloacas)", "numerico", "%", False, "INDEC", 4,
        [77.2, 77.25, 77.3, 77.35, 77.4, 77.42, 77.45, 77.48, 77.5, 77.53, 77.55, 77.58, 77.6, 77.6],
        [74.0, 74.5, 75.0, 75.3, 75.6, 76.0, 76.4, 76.8, 77.2, 77.6],
        None, "+0.4pp interanual", "up",
    ),
    # -- percepcion --------------------------------------------------------------
    (
        "confianza_consumidor", "percepcion", "Confianza del consumidor (ICC)", "numerico", "puntos", False, "Universidad Torcuato Di Tella", 1,
        [44.0, 44.3, 44.5, 44.7, 44.9, 45.1, 45.3, 45.4, 45.5, 45.6, 45.7, 45.8, 45.9, 46.0],
        [44.9, 39.4, 34.4, 38.8, 36.6, 38.4, 33.7, 41.0, 44.5, 46.0],
        None, "+0.1pt en el mes", "up",
    ),
    (
        "expectativas_inflacion", "percepcion", "Expectativas de inflación (REM, 12 meses)", "numerico", "%", False, "BCRA", 2,
        [95, 88, 82, 77, 73, 69, 65, 62, 60, 58, 57, 56, 55.5, 55],
        [19.6, 30.8, 40.1, 50.4, 51.6, 100.1, 180.0, 220.0, 90.0, 55.0],
        None, "-0.5pp en el mes", "down",
    ),
    (
        "humor_social", "percepcion", "Índice de humor social", "numerico", "puntos", False, "Management & Fit", 3,
        [47.5, 47.8, 48.1, 48.4, 48.7, 49.0, 49.3, 49.6, 49.8, 50.0, 50.3, 50.6, 50.8, 51.0],
        [52, 45, 38, 35, 40, 37, 33, 42, 48, 51],
        None, "+0.2pt en el mes", "up",
    ),
    (
        "aprobacion_gobierno", "percepcion", "Aprobación de gestión de gobierno", "numerico", "%", False, "Management & Fit", 4,
        [46.5, 46.2, 45.9, 45.6, 45.3, 45.0, 44.7, 44.4, 44.1, 43.8, 43.5, 43.3, 43.1, 43.0],
        [55, 40, 33, 55, 38, 32, 28, 48, 45, 43],
        None, "-0.5pp en el mes", "down",
    ),
    # -- seguridad -----------------------------------------------------------
    (
        "tasa_homicidios", "seguridad", "Tasa de homicidios", "numerico", "cada 100k hab.", False, "Ministerio de Seguridad", 1,
        [5.3, 5.3, 5.2, 5.2, 5.1, 5.1, 5.0, 5.0, 4.9, 4.9, 4.8, 4.8, 4.7, 4.7],
        [5.9, 5.7, 5.6, 4.6, 5.0, 5.1, 5.4, 5.2, 5.0, 4.7],
        None, "-0.1 cada 100k interanual", "down",
    ),
    (
        "delitos_propiedad", "seguridad", "Delitos contra la propiedad", "numerico", "%", False, "Ministerio de Seguridad", 2,
        [3.5, 3.2, 3.0, 2.8, 2.5, 2.2, 2.0, 1.8, 1.5, 1.2, 1.0, 0.8, 0.5, 0.3],
        [8.0, 6.5, 5.0, -12.0, 15.0, 10.0, 7.0, 5.0, 2.0, 0.3],
        None, "-0.2pp vs. mes anterior", "down",
    ),
    (
        "tasa_encarcelamiento", "seguridad", "Tasa de encarcelamiento", "numerico", "cada 100k hab.", False, "SNEEP - Ministerio de Justicia", 3,
        [228, 228, 229, 229, 230, 230, 231, 231, 232, 232, 233, 233, 234, 234],
        [175, 190, 205, 215, 220, 222, 225, 228, 231, 234],
        None, "+0.2 cada 100k en el mes", "up",
    ),
    (
        "percepcion_inseguridad", "seguridad", "Percepción de inseguridad", "numerico", "puntos", False, "Observatorio de la Deuda Social Argentina (UCA)", 4,
        [68, 67, 67, 66, 66, 65, 65, 64, 64, 63, 63, 62, 62, 61],
        [72, 74, 77, 68, 73, 76, 80, 78, 73, 61],
        None, "-0.5pt en el mes", "down",
    ),
    # -- desarrollo_militar ----------------------------------------------------
    (
        "gasto_defensa", "desarrollo_militar", "Gasto en defensa", "numerico", "% PBI", False, "SIPRI", 1,
        [0.82, 0.82, 0.83, 0.83, 0.84, 0.84, 0.85, 0.85, 0.86, 0.86, 0.87, 0.87, 0.88, 0.88],
        [0.86, 0.81, 0.76, 0.72, 0.75, 0.78, 0.80, 0.79, 0.83, 0.88],
        None, "+0.01pp interanual", "up",
    ),
    (
        "efectivos_ffaa", "desarrollo_militar", "Efectivos de las Fuerzas Armadas", "numerico", "miles", False, "Ministerio de Defensa", 2,
        [73.0, 73.0, 73.1, 73.1, 73.2, 73.2, 73.3, 73.3, 73.4, 73.4, 73.5, 73.5, 73.6, 73.6],
        [78, 76, 75, 74, 73, 72, 72, 73, 73, 73.6],
        None, "+0.1 mil en el mes", "up",
    ),
    (
        "inversion_equipamiento", "desarrollo_militar", "Inversión en equipamiento", "numerico", "% del presupuesto", False, "Ministerio de Defensa", 3,
        [8.0, 8.1, 8.3, 8.5, 8.7, 8.9, 9.1, 9.3, 9.5, 9.7, 9.9, 10.1, 10.3, 10.5],
        [4.5, 5.0, 5.5, 4.0, 5.2, 6.0, 7.0, 7.5, 9.0, 10.5],
        None, "+0.2pp en el mes", "up",
    ),
    (
        "ranking_poder_militar", "desarrollo_militar", "Ranking de poder militar (Global Firepower)", "numerico", "posición", False, "Global Firepower", 4,
        [34, 34, 33, 33, 33, 32, 32, 32, 31, 31, 31, 30, 30, 30],
        [38, 37, 36, 35, 34, 33, 33, 32, 31, 30],
        None, "-1 posición interanual", "down",
    ),
    (
        "acuerdo_fmi", "geo", "Acuerdo con el FMI", "cualitativo", "", False, "FMI", 1,
        None, None, "En revisión", "próximo desembolso: oct.", "flat",
    ),
    (
        "calificacion_soberana", "geo", "Calificación soberana", "cualitativo", "", False, "S&P Global Ratings", 2,
        None, None, "CCC+", "perspectiva positiva (S&P)", "up",
    ),
    (
        "swap_china", "geo", "Swap con China", "cualitativo", "", False, "BCRA", 3,
        None, None, "US$ 5.000 M activos", "sin cambios en el trimestre", "flat",
    ),
    (
        "mercosur_ue", "geo", "Mercosur–UE", "cualitativo", "", False, "Mercosur", 4,
        None, None, "Acuerdo firmado", "pendiente ratificación", "up",
    ),
]

NOTICIAS = [
    ("macro", "Economía", date(2026, 9, 7), "La brecha cambiaria se achica por tercera semana consecutiva",
     "El spread entre el dólar oficial y el blue cayó a su nivel más bajo en ocho meses, impulsado por la mayor oferta de divisas del agro."),
    ("macro", "Economía", date(2026, 9, 4), "El Banco Central acumuló reservas por cuarta semana al hilo",
     "Las compras se explican por la liquidación del agro y una mayor demanda de pesos estacional."),
    ("empleo", "Trabajo", date(2026, 9, 6), "El salario real mostró la primera mejora mensual del año",
     "Paritarias por encima de la inflación en tres sectores clave frenaron, por ahora, la caída del poder adquisitivo."),
    ("empleo", "Trabajo", date(2026, 9, 2), "Crece el empleo registrado en la construcción",
     "Es el tercer mes de recuperación tras la fuerte caída del año pasado, según datos del Ministerio de Trabajo."),
    ("geo", "Geopolítica", date(2026, 9, 6), "El Gobierno negocia un nuevo tramo de desembolsos con el FMI",
     "La misión del organismo llega a Buenos Aires la semana próxima para revisar el cumplimiento de las metas fiscales del segundo semestre."),
    ("geo", "Geopolítica", date(2026, 9, 3), "Avanza la ratificación del acuerdo Mercosur–Unión Europea",
     "Cancillería espera que el tratado esté listo para su firma definitiva antes de fin de año."),
]

TIMELINE = [
    (date(2026, 9, 7), "Brecha cambiaria en su mínimo de 8 meses", "positivo", "macro"),
    (date(2026, 9, 6), "Salario real mejora por primera vez en el año", "positivo", "empleo"),
    (date(2026, 9, 6), "Misión del FMI llega para revisar metas fiscales", "neutral", "geo"),
    (date(2026, 9, 4), "BCRA acumula reservas por cuarta semana consecutiva", "positivo", "macro"),
    (date(2026, 9, 3), "Avanza la ratificación del acuerdo Mercosur–UE", "positivo", "geo"),
    (date(2026, 9, 2), "Sube el empleo registrado en la construcción", "positivo", "empleo"),
    (date(2026, 8, 29), "Suba en la tasa de desempleo del segundo trimestre", "negativo", "empleo"),
    (date(2026, 8, 27), "S&P sube la perspectiva de la calificación soberana", "positivo", "geo"),
    (date(2026, 8, 22), "El dólar blue subió tres ruedas seguidas", "negativo", "macro"),
    (date(2026, 8, 18), "Cae la producción industrial por segundo mes", "negativo", "macro"),
    (date(2026, 8, 14), "Tensión comercial por trabas para importar insumos", "negativo", "geo"),
    (date(2026, 8, 9), "Se recupera el poder de compra del salario mínimo", "positivo", "empleo"),
    (date(2026, 8, 5), "El Merval marcó un nuevo máximo en pesos", "positivo", "macro"),
    (date(2026, 7, 30), "El Gobierno cerró el acuerdo técnico con el FMI", "positivo", "geo"),
    (date(2026, 7, 24), "Aumentó la informalidad laboral en el segundo trimestre", "negativo", "empleo"),
    (date(2026, 7, 19), "Moody's mantuvo la calificación soberana sin cambios", "neutral", "geo"),
    (date(2026, 7, 11), "La inflación núcleo volvió a acelerarse", "negativo", "macro"),
    (date(2026, 7, 3), "Se creó empleo privado por primera vez en el año", "positivo", "empleo"),
]


class Command(BaseCommand):
    help = "Carga datos de ejemplo (categorías, fuentes, indicadores, series, timeline, noticias)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Borra todos los datos de estas tablas antes de cargar el seed.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            IndicadorValor.objects.all().delete()
            EventoTimeline.objects.all().delete()
            Noticia.objects.all().delete()
            Indicador.objects.all().delete()
            Categoria.objects.all().delete()
            Fuente.objects.all().delete()
            self.stdout.write(self.style.WARNING("Datos previos borrados."))

        fuentes_por_nombre = {}
        for nombre, url in FUENTES:
            fuente, _ = Fuente.objects.get_or_create(nombre=nombre, defaults={"url": url})
            fuentes_por_nombre[nombre] = fuente

        for cat_id, nombre, color, icono, orden in CATEGORIAS:
            Categoria.objects.update_or_create(
                id=cat_id, defaults={"nombre": nombre, "color": color, "icono": icono, "orden": orden}
            )
        self.stdout.write(self.style.SUCCESS(f"{len(CATEGORIAS)} categorías OK."))
        self.stdout.write(self.style.SUCCESS(f"{len(FUENTES)} fuentes OK."))

        # Se acumulan TODOS los puntos en memoria y se escriben con un solo
        # bulk_create al final (ver más abajo) en vez de un update_or_create
        # por punto: contra una base remota (Neon) cada update_or_create es
        # 2 viajes de red (SELECT + INSERT/UPDATE) — con ~900 puntos eso son
        # ~1800 round-trips, varios minutos. bulk_create con
        # update_conflicts manda todo en un puñado de consultas ON CONFLICT
        # DO UPDATE, sin cambiar el resultado final.
        valores_a_guardar = []
        for (ind_id, cat_id, nombre, tipo, unidad, destacado, fuente_nombre, orden,
             mensuales, anuales, valor_actual, delta_texto, trend) in INDICADORES:
            indicador, _ = Indicador.objects.update_or_create(
                id=ind_id,
                defaults={
                    "categoria_id": cat_id,
                    "nombre": nombre,
                    "tipo": tipo,
                    "unidad": unidad,
                    "destacado": destacado,
                    "fuente": fuentes_por_nombre.get(fuente_nombre),
                    "orden": orden,
                    "actualizacion_automatica": ind_id in INDICADORES_CON_DATOS_REALES,
                    "polaridad": POLARIDADES.get(ind_id, "neutral"),
                },
            )

            if mensuales is not None:
                for fecha, valor in zip(PERIODOS_14M, mensuales):
                    es_ultimo = fecha == PERIODOS_14M[-1]
                    valores_a_guardar.append(IndicadorValor(
                        indicador=indicador, fecha=fecha, granularidad="mes",
                        valor_numerico=valor,
                        delta_texto=delta_texto if es_ultimo else "",
                        trend=trend if es_ultimo else "flat",
                    ))
            if anuales is not None:
                for fecha, valor in zip(ANIOS_10, anuales):
                    valores_a_guardar.append(IndicadorValor(
                        indicador=indicador, fecha=fecha, granularidad="anio", valor_numerico=valor,
                    ))
            if valor_actual is not None:
                # Indicadores sin serie histórica (destacados del header, o
                # cualitativos): un único punto "actual".
                es_texto = isinstance(valor_actual, str)
                valores_a_guardar.append(IndicadorValor(
                    indicador=indicador, fecha=date(2026, 9, 7), granularidad="dia",
                    valor_numerico=None if es_texto else valor_actual,
                    valor_texto=valor_actual if es_texto else "",
                    delta_texto=delta_texto, trend=trend,
                ))

        IndicadorValor.objects.bulk_create(
            valores_a_guardar,
            update_conflicts=True,
            unique_fields=["indicador", "fecha", "granularidad"],
            update_fields=["valor_numerico", "valor_texto", "delta_texto", "trend"],
            batch_size=500,
        )

        self.stdout.write(self.style.SUCCESS(f"{len(INDICADORES)} indicadores OK ({len(valores_a_guardar)} valores)."))

        for fecha, titulo, sentimiento, cat_id in TIMELINE:
            EventoTimeline.objects.update_or_create(
                fecha=fecha, titulo=titulo,
                defaults={"categoria_id": cat_id, "sentimiento": sentimiento},
            )
        self.stdout.write(self.style.SUCCESS(f"{len(TIMELINE)} eventos de timeline OK."))

        for cat_id, kicker, fecha, titulo, bajada in NOTICIAS:
            Noticia.objects.update_or_create(
                titulo=titulo,
                defaults={"categoria_id": cat_id, "kicker": kicker, "fecha": fecha, "bajada": bajada, "publicado": True},
            )
        self.stdout.write(self.style.SUCCESS(f"{len(NOTICIAS)} noticias OK."))

        self.stdout.write(self.style.SUCCESS("Seed completo."))
