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
    ("educacion", "Educación", "#2C5F7A", "GraduationCap", 12),
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
    ("OCDE (PISA)", "https://www.oecd.org/pisa/"),
    ("Argentinos por la Educación", "https://argentinosporlaeducacion.org/"),
    ("OPSA-UBA", "https://www.psi.uba.ar/"),
    ("El Cronista", "https://www.cronista.com/"),
    ("Perfil", "https://www.perfil.com/"),
    ("BYMA (S&P MERVAL)", "https://www.byma.com.ar/"),
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
    'balanza_comercial', 'exportaciones', 'merval',
}

# A pedido explícito de no mostrar ningún número que no salga de una
# fuente real: este seed NO carga ningún IndicadorValor para los de
# INDICADORES_CON_DATOS_REALES (eso es trabajo exclusivo de
# fetch_datos_reales.py — sembrar acá un valor ilustrativo "de relleno"
# para esos, aunque luego se pisara, causó un bug real: la serie
# ilustrativa de inflación quedaba fechada el día 1 de cada mes y la real
# el último día hábil, así que no coincidían en la clave única
# (indicador+fecha+granularidad) y convivían las dos, haciendo zigzaguear
# el gráfico entre ~130% y ~33% mes a mes). Solo se cargan estos dos, que
# son un único punto verificado por búsqueda web (no una serie
# automática, pero tampoco inventado — ver el comentario en su tupla en
# INDICADORES). El resto de los 47 indicadores queda creado igual
# (nombre, unidad, metodología, fuente) para que el glosario los siga
# explicando, pero sin ninguna cifra hasta tener una fuente real.
INDICADORES_CON_VALORES_REALES = {
    'tasa_homicidios', 'ranking_poder_militar',
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
    # El dato real disponible es la POSICIÓN en el ranking del WJP Rule of
    # Law Index (63°, 65°...), no el puntaje 0-1 — ahí más bajo es mejor,
    # al revés de lo que asumía el 'positivo' original (pensado para un
    # puntaje). Mismo criterio que riesgo_pais/ranking_poder_militar.
    'estado_derecho': 'negativo',
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
    # educacion
    'resultados_pisa': 'positivo',
    'tasa_escolarizacion': 'positivo',
    'tasa_analfabetismo': 'negativo',
    # 'gasto_educativo' queda neutral a propósito, mismo criterio que
    # gasto_publico/gasto_defensa: cuánto se gasta es una discusión de
    # política, no tiene una dirección "mejor" consensuada por sí sola.
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
        # Auto-actualizable desde hoy (BYMA, ver fetch_datos_reales.py) —
        # el valor de este tuple no se usa (Merval no está en
        # INDICADORES_CON_VALORES_REALES), pero se deja fuente_nombre
        # correcto para que la tarjeta cite bien la fuente real.
        "merval", "macro", "Merval", "numerico", "pts", True, "BYMA (S&P MERVAL)", 0,
        None, None, None, "", "flat",
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
        # El dato real disponible es la POSICIÓN en el ranking (no el
        # puntaje 0-1 que tenía el viejo valor ilustrativo) — de ahí el
        # cambio de nombre y unidad para que no lean "0,52" como un
        # porcentaje o índice normalizado.
        "estado_derecho", "institucional", "Ranking de estado de derecho (WJP)", "numerico", "posición", False, "World Justice Project", 2,
        None, None, None, "", "flat",
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
        "humor_social", "percepcion", "Optimismo económico (humor social)", "numerico", "% optimista", False, "El Cronista", 3,
        None, None, None, "", "flat",
    ),
    (
        "aprobacion_gobierno", "percepcion", "Aprobación de gestión de gobierno", "numerico", "%", False, "Perfil", 4,
        None, None, None, "", "flat",
    ),
    # -- seguridad -----------------------------------------------------------
    (
        # Único punto real (no serie): Estadísticas Criminales 2025 del
        # Ministerio de Seguridad (SNIC), verificado por búsqueda web —
        # bajó de 4,4 en 2023 a 3,6 en 2025, la tasa más baja registrada
        # (ver noticia de seguridad en seed_noticias_reales.py). Sin serie
        # histórica fabricada alrededor: no hay una fuente automática para
        # esto, así que no se inventa una tendencia mes a mes.
        "tasa_homicidios", "seguridad", "Tasa de homicidios", "numerico", "cada 100k hab.", False, "Ministerio de Seguridad", 1,
        None, None, 3.6, "-0.8 vs. 2023 (SNIC, año 2025)", "down",
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
        "percepcion_inseguridad", "seguridad", "Percepción de inseguridad", "numerico", "puntos (0-10)", False, "OPSA-UBA", 4,
        None, None, None, "", "flat",
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
        # Único punto real (no serie): ranking 2026 publicado por Global
        # Firepower, verificado por búsqueda web — Argentina en la
        # posición 32 de 145 países. Sin serie histórica fabricada: GFP
        # publica una vez por año, no hay granularidad mensual real.
        "ranking_poder_militar", "desarrollo_militar", "Ranking de poder militar (Global Firepower)", "numerico", "posición", False, "Global Firepower", 4,
        None, None, 32, "32 de 145 países (Global Firepower 2026)", "flat",
    ),
    # -- educacion -------------------------------------------------------
    # Categoría nueva — sin datos ilustrativos de relleno (mismo criterio
    # que el resto desde la limpieza): los números viven en
    # seed_indicadores_reales.py, verificados por búsqueda web.
    (
        "resultados_pisa", "educacion", "Resultados PISA (matemática)", "numerico", "puntos", False, "OCDE (PISA)", 1,
        None, None, None, "", "flat",
    ),
    (
        "gasto_educativo", "educacion", "Gasto educativo nacional", "numerico", "% PBI", False, "Argentinos por la Educación", 2,
        None, None, None, "", "flat",
    ),
    (
        "tasa_escolarizacion", "educacion", "Tasa de escolarización (4 a 17 años)", "numerico", "%", False, "INDEC", 3,
        None, None, None, "", "flat",
    ),
    (
        "tasa_analfabetismo", "educacion", "Tasa de analfabetismo", "numerico", "%", False, "INDEC", 4,
        None, None, None, "", "flat",
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

# Vacío a propósito, mismo motivo que TIMELINE: eran 6 noticias inventadas
# sin medio ni link real (idénticas al MOCK_NOTICIAS del frontend), solo
# para probar el diseño de las tarjetas de noticias. Las noticias reales
# viven en `seed_noticias_reales.py` (verificadas por búsqueda web, con
# medio y url reales).
NOTICIAS = []

# Reemplaza la lista original de 18 titulares inventados (idéntica al
# MOCK_TIMELINE del frontend) por hechos reales — mismos que ya están
# verificados y sourceados en seed_noticias_reales.py, resumidos acá en
# formato de línea de tiempo (fecha, título corto, sentimiento, categoría).
TIMELINE = [
    (date(2023, 12, 5), "Argentina repite bajos resultados en las pruebas PISA", "negativo", "educacion"),
    (date(2023, 12, 13), "El Gobierno devalúa el peso 118% a dos días de asumir Milei", "negativo", "macro"),
    (date(2024, 3, 9), "Bullrich despliega fuerzas federales en Rosario tras la ola narco", "neutral", "seguridad"),
    (date(2024, 4, 16), "Argentina compra 24 aviones de combate F-16 a Dinamarca", "positivo", "desarrollo_militar"),
    (date(2024, 9, 26), "La pobreza trepa a 52,9%, la más alta en 20 años", "negativo", "pobreza"),
    (date(2024, 10, 3), "Milei veta la Ley de Financiamiento Universitario", "negativo", "educacion"),
    (date(2024, 11, 8), "El blanqueo de capitales supera los US$32.000 millones", "positivo", "sector_externo"),
    (date(2024, 12, 2), "El PAMI restringe el acceso a medicamentos gratis para jubilados", "negativo", "bienestar"),
    (date(2024, 12, 31), "Liquidación récord del agro: más de US$25.000 millones en 2024", "positivo", "produccion"),
    (date(2025, 1, 14), "La inflación de 2024 cierra en 117,8%, casi la mitad que el año anterior", "positivo", "macro"),
    (date(2025, 1, 17), "Argentina cierra 2024 con superávit fiscal por primera vez en 14 años", "positivo", "macro"),
    (date(2025, 4, 11), "Milei elimina el cepo cambiario tras 15 años de controles", "positivo", "macro"),
    (date(2025, 5, 3), "El Gobierno pone un techo de 1% mensual a los aumentos salariales", "negativo", "empleo"),
    (date(2025, 10, 14), "Trump recibe a Milei en la Casa Blanca y condiciona el apoyo a las elecciones", "neutral", "geo"),
    (date(2025, 10, 28), "El riesgo país cierra en mínimos de ocho años tras el triunfo electoral", "positivo", "macro"),
    (date(2026, 1, 22), "Argentina registra la menor tasa de homicidios de su historia", "positivo", "seguridad"),
    (date(2026, 2, 19), "La balanza comercial arranca 2026 con superávit de US$1.987 millones", "positivo", "sector_externo"),
    (date(2026, 5, 21), "El FMI aprueba la 2ª revisión y destraba un desembolso de US$1.000 millones", "positivo", "geo"),
    (date(2026, 7, 21), "S&P, Fitch y Moody's alinean a Argentina en B- por 1ª vez en una década", "positivo", "macro"),
    (date(2026, 9, 7), "Vuelve la inscripción al Servicio Militar Voluntario con edad ampliada", "neutral", "desarrollo_militar"),
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

            # Solo se cargan cifras para los indicadores con una fuente real
            # detrás (ver INDICADORES_CON_VALORES_REALES) — el resto queda
            # con su metodología documentada pero sin ningún IndicadorValor,
            # en vez de rellenar con series inventadas para que "se vea
            # completo".
            if ind_id in INDICADORES_CON_VALORES_REALES:
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
