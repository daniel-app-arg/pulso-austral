"""
Carga puntos reales sueltos para indicadores que no tienen una API que los
actualice solos, pero sí tienen datos publicados y verificables (búsqueda
web, con fuente citada en cada caso) — a diferencia de fetch_datos_reales.py
(series automáticas día a día) o del seed original (que rellenaba con
series inventadas para que "se viera completo", sacado a pedido explícito
de no mostrar ningún número sin respaldo real).

No es una serie continua ni interpolada: para cada indicador se cargan
tantos puntos como efectivamente se encontraron publicados (a veces 1, a
veces varios años/meses de una serie periódica real), nada más. Si un
indicador no aparece acá y no está en fetch_datos_reales.py, es porque no
se encontró una fuente pública confiable para reemplazar su antiguo valor
ilustrativo — queda "sin datos" en vez de inventarlo.

Uso:
    python manage.py seed_indicadores_reales
"""

from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from indicadores.models import Indicador, IndicadorValor

# (indicador_id, granularidad, fecha, valor_numerico | None, valor_texto,
#  delta_texto, trend)
# valor_numerico y valor_texto son mutuamente excluyentes (numerico vs.
# cualitativo, según Indicador.tipo).
PUNTOS: list[tuple[str, str, date, float | None, str, str, str]] = [
    # -- percepcion (UTDT, BCRA-REM, encuestas) --------------------------
    ('confianza_consumidor', 'mes', date(2025, 1, 1), 47.38, '', 'pico de la era Milei', 'up'),
    ('confianza_consumidor', 'mes', date(2026, 8, 1), 40.23, '', '-1,08% en el mes, +0,71% interanual (UTDT)', 'down'),
    ('expectativas_inflacion', 'mes', date(2026, 8, 1), 21.8, '', '-0,5pp vs. relevamiento anterior — REM BCRA, a 12 meses', 'down'),
    ('humor_social', 'mes', date(2026, 8, 1), 30.8, '', 'optimismo económico, mínimo del año (El Cronista)', 'down'),
    ('aprobacion_gobierno', 'mes', date(2026, 8, 1), 34, '', 'Perfil / QMonitor, ago-2026', 'flat'),
    # -- geo (cualitativos) -----------------------------------------------
    ('calificacion_soberana', 'mes', date(2026, 7, 21), None, 'B-',
     'S&P, Fitch y Moody’s alineadas en B- por 1ra vez en una década (antes CCC+/Caa1)', 'up'),
    ('acuerdo_fmi', 'mes', date(2026, 5, 21), None, '2ª revisión aprobada (EFF)',
     'desembolso de US$1.000M destrabado', 'flat'),
    ('swap_china', 'mes', date(2026, 8, 1), None, 'US$19.000 M renovado a 5 años',
     'tramo usado casi devuelto (de US$5.000M a ~US$679M)', 'flat'),
    ('mercosur_ue', 'mes', date(2026, 5, 1), None, 'Interino en aplicación provisional',
     'firmado 17-ene-2026, pendiente ratificación completa', 'up'),
    # -- institucional ------------------------------------------------------
    ('cpi_corrupcion', 'anio', date(2019, 1, 1), 45, '', 'máximo histórico de la serie', 'flat'),
    ('cpi_corrupcion', 'anio', date(2024, 1, 1), 37, '', '', 'flat'),
    ('cpi_corrupcion', 'anio', date(2025, 1, 1), 36, '', '-1 pto vs. 2024, puesto 104° (Transparencia Internacional, feb-2026)', 'down'),
    ('estado_derecho', 'anio', date(2024, 1, 1), 63, '', 'de 142 países', 'flat'),
    ('estado_derecho', 'anio', date(2025, 1, 1), 65, '', '+2 posiciones (peor), de 143 países — WJP Rule of Law Index', 'up'),
    ('gasto_publico', 'mes', date(2025, 12, 1), 14.5, '', 'mínimo de la última década (Ámbito Financiero)', 'flat'),
    ('confianza_gobierno', 'mes', date(2026, 6, 1), 2.07, '', 'primera suba de 2026 (escala 0-5)', 'up'),
    ('confianza_gobierno', 'mes', date(2026, 7, 1), 1.94, '', 'mínimo de la era Milei', 'down'),
    ('confianza_gobierno', 'mes', date(2026, 8, 1), 2.06, '', '+6,4% vs. julio — UTDT (ICG)', 'up'),
    # -- bienestar ------------------------------------------------------
    ('esperanza_vida', 'anio', date(2024, 1, 1), 77.5, '', 'Banco Mundial', 'flat'),
    ('cobertura_salud', 'anio', date(2023, 1, 1), 67.5, '', '2do semestre — obra social, prepaga o mutual', 'flat'),
    ('cobertura_salud', 'anio', date(2025, 1, 1), 65.4, '', '-2,1pp vs. 2023, 2do semestre — INDEC (EPH)', 'down'),
    ('mortalidad_infantil', 'anio', date(2023, 1, 1), 8.0, '', '', 'flat'),
    ('mortalidad_infantil', 'anio', date(2024, 1, 1), 8.5, '', '+6,25% interanual — Ministerio de Salud (DEIS)', 'up'),
    ('acceso_servicios', 'anio', date(2010, 1, 1), 53.8, '', 'cloacas — INDEC Censo', 'flat'),
    ('acceso_servicios', 'anio', date(2022, 1, 1), 62.6, '', 'cloacas, +8,8pp vs. 2010 — INDEC Censo 2022', 'up'),
    # -- seguridad (además de tasa_homicidios, ya cargado en el seed) ---
    ('delitos_propiedad', 'anio', date(2025, 1, 1), -21.2, '',
     '399.676 robos en 2025 vs. 506.927 en 2024 — Ministerio de Seguridad', 'down'),
    ('tasa_encarcelamiento', 'anio', date(2024, 12, 31), 256, '', 'récord histórico — SNEEP', 'flat'),
    ('percepcion_inseguridad', 'mes', date(2026, 6, 1), 7.3, '',
     'sobre 10 — Monitor de Inseguridad, OPSA-UBA', 'flat'),
    # -- desarrollo_militar ----------------------------------------------
    ('gasto_defensa', 'anio', date(2010, 1, 1), 0.75, '', 'SIPRI', 'flat'),
    ('gasto_defensa', 'anio', date(2020, 1, 1), 0.63, '', 'SIPRI', 'flat'),
    ('gasto_defensa', 'anio', date(2021, 1, 1), 0.65, '', 'SIPRI', 'flat'),
    ('gasto_defensa', 'anio', date(2025, 1, 1), 0.56, '', 'mínimo relativo de la serie — SIPRI 2026', 'down'),
    ('efectivos_ffaa', 'anio', date(2015, 1, 1), 77.0, '', 'Ministerio de Defensa', 'flat'),
    ('efectivos_ffaa', 'anio', date(2018, 1, 1), 83.0, '', 'Ministerio de Defensa', 'flat'),
    ('efectivos_ffaa', 'anio', date(2023, 1, 1), 88.2, '', 'incluye la baja voluntaria de 15.415 efectivos desde dic-2023', 'flat'),
    # -- macro ------------------------------------------------------------
    ('riesgo_pais', 'dia', date(2026, 9, 3), 494, '', '-1,2% ese día — Rava Bursátil', 'down'),
    ('resultado_fiscal', 'mes', date(2026, 3, 1), 0.5, '', 'acumulado 1er trimestre — Ministerio de Economía', 'flat'),
    ('resultado_fiscal', 'mes', date(2026, 6, 1), 0.6, '', 'acumulado a junio', 'up'),
    ('resultado_fiscal', 'mes', date(2026, 7, 1), 0.9, '', 'acumulado a julio — meta anual 1,4-1,5% PBI', 'up'),
    # -- empleo -----------------------------------------------------------
    # Actualización de los últimos 3 años (sep-2023 a sep-2026), a pedido
    # explícito. De paso corrige un problema real que encontró la
    # investigación: los 3 puntos de empleo_informal que había cargado
    # antes en 2025-2026 (42,0 / 43,0 / 44,2) en realidad medían la "tasa
    # de informalidad general" de INDEC (asalariados + cuentapropistas
    # informales) — una métrica DISTINTA a la que define este indicador
    # ("asalariados sin descuento jubilatorio", ver METODOLOGIAS en
    # seed_pulso_austral.py) y a la que usan todos los puntos históricos
    # 2015-2023 ya cargados. Quedaban mezcladas dos series distintas en
    # el mismo indicador, lo que rompía la comparación de tendencia. Se
    # reemplazan por la serie correcta en las mismas fechas (el upsert
    # por indicador+fecha+granularidad las pisa solas). Mismo criterio
    # para salario_real: se estandariza en la variación del índice de
    # salarios "nivel general" (nominal vs. IPC, ambos interanuales),
    # que es la que describe la metodología del indicador — se excluyen
    # a propósito dos puntos que la investigación encontró (ene y
    # mar-2026) por estar medidos en base a "salarios registrados"
    # (excluye informales), una serie distinta que hubiera generado un
    # quiebre artificial en la tendencia.
    ('salario_real', 'mes', date(2023, 11, 1), -6.4, '', 'nov-2023, nominal +144,3% vs IPC +160,9% — INDEC/Infobae', 'flat'),
    ('salario_real', 'mes', date(2024, 1, 1), -20.7, '', 'ene-2024, nominal +181,0% vs IPC +254,2% — INDEC/Infobae', 'down'),
    ('salario_real', 'mes', date(2024, 5, 1), -16.0, '', 'may-2024, nominal +216,0% vs IPC +276,4% — INDEC/Cronista', 'up'),
    ('salario_real', 'mes', date(2024, 7, 1), -15.7, '', 'jul-2024, nominal +206,2% vs IPC +263,4% — INDEC', 'up'),
    ('salario_real', 'mes', date(2024, 8, 1), -10.7, '', 'ago-2024, nominal +200,6% vs IPC +236,7% — INDEC/iProfesional', 'up'),
    ('salario_real', 'mes', date(2024, 9, 1), -8.8, '', 'sep-2024, nominal +181,9% vs IPC +209,0% — INDEC/La Nación', 'up'),
    ('salario_real', 'mes', date(2024, 12, 1), 12.7, '', 'dic-2024, nominal +145,5% vs IPC +117,8% — primer mes que le gana a la inflación', 'up'),
    ('salario_real', 'mes', date(2025, 1, 1), 17.6, '', 'ene-2025, nominal +117,0% vs IPC +84,5% — INDEC', 'up'),
    ('salario_real', 'mes', date(2025, 9, 1), 10.8, '', 'sep-2025, nominal +46,0% vs IPC +31,8% — INDEC', 'down'),
    ('salario_real', 'mes', date(2025, 12, 1), 5.1, '', 'dic-2025, nominal +38,2% vs IPC +31,5% — INDEC', 'down'),
    ('salario_real', 'mes', date(2026, 4, 1), 3.4, '', 'abr-2026, nivel general, nominal +36,9% vs IPC +32,4% — INDEC/Cronista', 'down'),
    ('salario_real', 'mes', date(2026, 6, 1), 1.6, '', 'jun-2026, nominal +35,7% vs IPC ~33,55% (Trading Economics) — INDEC', 'down'),
    ('empleo_informal', 'mes', date(2023, 1, 1), 36.7, '', '1er trim. 2023, asalariados sin descuento jubilatorio — INDEC (EPH)', 'flat'),
    ('empleo_informal', 'mes', date(2023, 4, 1), 36.8, '', '2do trim. 2023, asalariados sin descuento jubilatorio — INDEC (EPH)', 'up'),
    ('empleo_informal', 'mes', date(2023, 7, 1), 36.7, '', '3er trim. 2023, asalariados sin descuento jubilatorio — INDEC (EPH)', 'down'),
    ('empleo_informal', 'mes', date(2024, 1, 1), 35.7, '', '1er trim. 2024, asalariados sin descuento jubilatorio — INDEC (EPH)', 'down'),
    ('empleo_informal', 'mes', date(2024, 4, 1), 36.4, '', '2do trim. 2024, asalariados sin descuento jubilatorio — INDEC (EPH)', 'up'),
    ('empleo_informal', 'mes', date(2024, 7, 1), 36.7, '', '3er trim. 2024, asalariados sin descuento jubilatorio — INDEC (EPH)', 'up'),
    ('empleo_informal', 'mes', date(2024, 10, 1), 36.1, '', '4to trim. 2024, -0,6pp vs. trim. anterior — INDEC (EPH)', 'down'),
    ('empleo_informal', 'mes', date(2025, 1, 1), 36.3, '', '1er trim. 2025, asalariados sin descuento jubilatorio — INDEC (EPH)', 'up'),
    ('empleo_informal', 'mes', date(2025, 4, 1), 37.7, '', '2do trim. 2025, +1,4pp vs. trim. anterior — INDEC (EPH)', 'up'),
    ('empleo_informal', 'mes', date(2025, 7, 1), 36.7, '', '3er trim. 2025, -1,0pp vs. trim. anterior — INDEC (EPH)', 'down'),
    ('empleo_informal', 'mes', date(2025, 10, 1), 36.3, '', '4to trim. 2025, -0,4pp vs. trim. anterior — INDEC (EPH)', 'down'),
    ('empleo_informal', 'mes', date(2026, 1, 1), 37.9, '', '1er trim. 2026, +1,6pp vs. trim. anterior — INDEC (EPH)', 'up'),
    ('canasta_basica', 'mes', date(2024, 1, 1), 596823, '', 'familia tipo, ene-2024, +20,4% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 2, 1), 690901.57, '', 'familia tipo, feb-2024, +15,8% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 3, 1), 773385.10, '', 'familia tipo, mar-2024, +11,9% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 5, 1), 851351, '', 'familia tipo, may-2024 (fecha inferida por consistencia) — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 6, 1), 873169, '', 'familia tipo, jun-2024 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 7, 1), 900648, '', 'familia tipo, jul-2024, +263,4% interanual — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 8, 1), 939887, '', 'familia tipo, ago-2024 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 9, 1), 964620, '', 'familia tipo, sep-2024, +2,6% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 10, 1), 986586, '', 'familia tipo, oct-2024, +2,3% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 11, 1), 1001466, '', 'familia tipo, nov-2024, superó el millón por primera vez — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2024, 12, 1), 1024435, '', 'familia tipo, dic-2024, +106,6% interanual — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 1, 1), 1033716, '', 'familia tipo, ene-2025, +0,9% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 2, 1), 1057923, '', 'familia tipo, feb-2025, +53,1% interanual — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 3, 1), 1100267, '', 'familia tipo, mar-2025, +4% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 4, 1), 1110063, '', 'familia tipo, abr-2025, +0,9% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 6, 1), 1128398, '', 'familia tipo — INDEC', 'flat'),
    ('canasta_basica', 'mes', date(2025, 7, 1), 1149353, '', 'familia tipo, jul-2025, +27,6% interanual — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 8, 1), 1160780, '', 'familia tipo, ago-2025 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 9, 1), 1176852, '', 'familia tipo, sep-2025 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 10, 1), 1213799, '', 'familia tipo, oct-2025 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 11, 1), 1257329.03, '', 'familia tipo, nov-2025 (GBA) — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2025, 12, 1), 1308713, '', 'familia tipo, dic-2025 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2026, 2, 1), 1397672, '', 'familia tipo, feb-2026 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2026, 3, 1), 1434464, '', 'familia tipo, mar-2026 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2026, 4, 1), 1469768, '', 'familia tipo, abr-2026 — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2026, 5, 1), 1498741, '', 'familia tipo, may-2026, +2% en el mes — INDEC', 'up'),
    ('canasta_basica', 'mes', date(2026, 7, 1), 1564716, '', '+36,1% interanual — INDEC, jul-2026', 'up'),
    # -- pobreza ------------------------------------------------------------
    ('tasa_pobreza', 'mes', date(2024, 1, 1), 52.9, '', '1er semestre, pico post-devaluación — INDEC (EPH)', 'flat'),
    ('tasa_pobreza', 'mes', date(2024, 7, 1), 38.1, '', '2do semestre', 'down'),
    ('tasa_pobreza', 'mes', date(2025, 7, 1), 28.2, '', '-9,9pp vs. 2do sem. 2024 — INDEC (EPH)', 'down'),
    ('tasa_indigencia', 'mes', date(2024, 7, 1), 8.2, '', '2do semestre — INDEC (EPH)', 'flat'),
    ('tasa_indigencia', 'mes', date(2025, 7, 1), 6.3, '', '-1,9pp vs. 2do sem. 2024', 'down'),
    ('gini', 'mes', date(2024, 10, 1), 0.430, '', '4to trimestre — INDEC (EPH)', 'flat'),
    ('gini', 'mes', date(2025, 10, 1), 0.427, '', 'leve mejora interanual, 4to trimestre', 'down'),
    ('brecha_ingresos', 'mes', date(2025, 10, 1), 13, '', 'decil 10 vs. decil 1, ingreso per cápita familiar — INDEC (EPH)', 'flat'),
    # -- produccion -----------------------------------------------------
    ('ipi_manufacturero', 'mes', date(2026, 5, 1), -5.7, '', 'interanual — INDEC', 'flat'),
    ('ipi_manufacturero', 'mes', date(2026, 6, 1), 2.0, '', 'interanual, acumulado ene-jun -2,2% — INDEC', 'up'),
    ('capacidad_instalada', 'mes', date(2026, 1, 1), 53.6, '', 'INDEC', 'flat'),
    ('capacidad_instalada', 'mes', date(2026, 3, 1), 59.8, '', 'INDEC', 'up'),
    ('capacidad_instalada', 'mes', date(2026, 4, 1), 59.9, '', 'INDEC', 'up'),
    ('capacidad_instalada', 'mes', date(2026, 5, 1), 58.4, '', 'INDEC', 'down'),
    ('capacidad_instalada', 'mes', date(2026, 6, 1), 59.1, '', '+0,2pp interanual vs. jun-2025 (58,9%) — INDEC', 'up'),
    ('produccion_agropecuaria', 'anio', date(2026, 1, 1), 163.3, '', 'campaña 2025/26 récord — soja 50,1M t (+5%) y maíz 64M t (Bolsa de Cereales / Gobierno)', 'up'),
    # -- sector_externo ------------------------------------------------
    ('cuenta_corriente', 'anio', date(2026, 1, 1), 0.7, '', 'proyección Morgan Stanley — 1er superávit anual en 7 años', 'up'),
    ('deuda_externa', 'mes', date(2025, 3, 1), 278.073, '', '1er trimestre — BCRA', 'flat'),
    ('deuda_externa', 'mes', date(2025, 9, 1), 316.935, '', '3er trimestre — BCRA', 'up'),
    # -- educacion --------------------------------------------------------
    ('resultados_pisa', 'anio', date(2022, 1, 1), 378, '', '66° de 81 países en Matemática — OCDE, PISA 2022', 'flat'),
    ('resultados_pisa', 'anio', date(2025, 1, 1), 367, '', '367 pts, mínimo histórico, puesto 75/91 — OCDE=482, solo 24% supera nivel básico', 'down'),
    ('gasto_educativo', 'anio', date(2024, 1, 1), 0.88, '', 'Estado nacional, sin provincias', 'flat'),
    ('gasto_educativo', 'anio', date(2025, 1, 1), 0.73, '', 'mínimo de los últimos 20 años', 'down'),
    ('gasto_educativo', 'anio', date(2026, 1, 1), 0.75, '', 'Argentinos por la Educación, presupuesto 2026', 'up'),
    ('tasa_escolarizacion', 'anio', date(2022, 1, 1), 97.6, '', 'de 4 a 17 años — INDEC (Censo 2022)', 'flat'),
    ('tasa_analfabetismo', 'anio', date(2010, 1, 1), 1.9, '', 'último dato censal — el Censo 2022 no incluyó esta pregunta', 'flat'),
    # -- históricos, transiciones de gobierno (para "Por gobierno") ------
    # No cubre todos los indicadores ni todas las transiciones — es lo que
    # se pudo verificar por búsqueda web en esta pasada. dólar oficial y
    # reservas BCRA de la gestión Milei ya no necesitan puntos manuales:
    # se amplió VENTANA_DIARIA en fetch_datos_reales.py para que la serie
    # real del BCRA cubra desde antes de su asunción.
    #
    # Inflación interanual — INDEC, diciembre de cada año. El propio INDEC
    # reconoció la intervención de las estadísticas oficiales entre 2007 y
    # 2015: estos valores son los oficiales de la época, no una
    # reconstrucción — se aclara en el delta porque en general se los
    # considera subestimados (ver notas de Wikipedia/prensa económica).
    #
    # Cada valor de un límite de mandato se carga DOS veces (9-dic y
    # 11-dic) para que sirva de "AL FINAL" del gobierno saliente y de "AL
    # INICIO" del entrante — si se cargara una sola vez, Django la asigna
    # a un solo gobierno según el rango de fechas (`fecha_inicio`/
    # `fecha_fin` no se solapan) y el otro queda con un solo punto (0% de
    # variación, no realmente "sin datos" pero engañoso igual).
    ('inflacion_interanual', 'mes', date(2003, 12, 1), 3.6, '', 'INDEC, dic-2003 (inicio N. Kirchner)', 'flat'),
    ('inflacion_interanual', 'mes', date(2007, 12, 9), 8.5, '', 'INDEC oficial, dic-2007 — cuestionado por la intervención del INDEC 2007-2015', 'flat'),
    ('inflacion_interanual', 'mes', date(2007, 12, 11), 8.5, '', 'INDEC oficial, dic-2007 — cuestionado por la intervención del INDEC 2007-2015', 'flat'),
    ('inflacion_interanual', 'mes', date(2011, 12, 9), 9.5, '', 'INDEC oficial, dic-2011 — consultoras privadas estimaban ~22,8%', 'flat'),
    ('inflacion_interanual', 'mes', date(2011, 12, 11), 9.5, '', 'INDEC oficial, dic-2011 — consultoras privadas estimaban ~22,8%', 'flat'),
    ('inflacion_interanual', 'mes', date(2015, 12, 9), 25.0, '', 'INDEC oficial, dic-2015 — último año de la intervención, cuestionado', 'flat'),
    ('inflacion_interanual', 'mes', date(2015, 12, 11), 25.0, '', 'INDEC oficial, dic-2015 — último año de la intervención, cuestionado', 'flat'),
    ('inflacion_interanual', 'mes', date(2019, 12, 9), 53.8, '', 'INDEC, dic-2019', 'flat'),
    ('inflacion_interanual', 'mes', date(2019, 12, 11), 53.8, '', 'INDEC, dic-2019', 'flat'),
    # Desempleo — INDEC (EPH), promedio o trimestre de cierre de cada año.
    ('desempleo', 'mes', date(2003, 12, 1), 17.3, '', 'INDEC (EPH), promedio 2003 (inicio N. Kirchner)', 'flat'),
    ('desempleo', 'mes', date(2007, 12, 9), 8.5, '', 'INDEC (EPH), promedio 2007', 'flat'),
    ('desempleo', 'mes', date(2007, 12, 11), 8.5, '', 'INDEC (EPH), promedio 2007', 'flat'),
    ('desempleo', 'mes', date(2011, 12, 9), 7.2, '', 'INDEC (EPH), promedio 2011', 'flat'),
    ('desempleo', 'mes', date(2011, 12, 11), 7.2, '', 'INDEC (EPH), promedio 2011', 'flat'),
    ('desempleo', 'mes', date(2015, 12, 9), 7.6, '', 'INDEC (EPH), promedio 2015', 'flat'),
    ('desempleo', 'mes', date(2015, 12, 11), 7.6, '', 'INDEC (EPH), promedio 2015', 'flat'),
    ('desempleo', 'mes', date(2019, 12, 9), 9.8, '', 'INDEC (EPH), promedio 2019', 'flat'),
    ('desempleo', 'mes', date(2019, 12, 11), 9.8, '', 'INDEC (EPH), promedio 2019', 'flat'),
    # Dólar oficial — sólo hasta 2019 (2003-2015 con fuentes de cotización
    # histórica; el tramo de Milei ya lo cubre el fetch real del BCRA).
    ('dolar_oficial', 'mes', date(2003, 5, 25), 2.94, '', 'cotización histórica BCRA, asunción N. Kirchner', 'flat'),
    ('dolar_oficial', 'mes', date(2007, 12, 9), 3.15, '', 'cotización histórica BCRA, dic-2007', 'flat'),
    ('dolar_oficial', 'mes', date(2007, 12, 11), 3.15, '', 'cotización histórica BCRA, dic-2007', 'flat'),
    ('dolar_oficial', 'mes', date(2011, 12, 9), 4.30, '', 'inicio del cepo cambiario, nov-2011', 'flat'),
    ('dolar_oficial', 'mes', date(2011, 12, 11), 4.30, '', 'inicio del cepo cambiario, nov-2011', 'flat'),
    ('dolar_oficial', 'mes', date(2015, 12, 9), 9.83, '', 'último día antes de que Macri levantara el cepo', 'flat'),
    ('dolar_oficial', 'mes', date(2015, 12, 11), 9.83, '', 'último día antes de que Macri levantara el cepo', 'flat'),
    ('dolar_oficial', 'mes', date(2019, 12, 9), 62.99, '', 'último día hábil del gobierno de Macri', 'flat'),
    ('dolar_oficial', 'mes', date(2019, 12, 11), 62.99, '', 'último día hábil del gobierno de Macri', 'flat'),
    # Fin del mandato de Alberto Fernández — el arranque de Milei ya lo
    # cubre el fetch real del BCRA (ver VENTANA_DIARIA), pero el cierre de
    # AF necesita este punto manual: la ventana real arranca 1 día después
    # de su límite a propósito, para no pisarle la comparación (ver nota
    # en fetch_datos_reales.py).
    ('dolar_oficial', 'mes', date(2023, 12, 9), 366.5, '', 'BCRA, último día hábil antes de la asunción de Milei', 'flat'),
    # Riesgo país (EMBI, JP Morgan) — sin serie histórica pública (ver
    # README), así que son puntos sueltos en las fechas que se pudieron
    # verificar, incluida la asunción de Milei (para que su propia
    # comparativa muestre un "AL INICIO" real y no el primer dato de hoy).
    ('riesgo_pais', 'dia', date(2007, 3, 1), 184, '', 'JP Morgan (EMBI+), principios de 2007 — mínimo de la era Kirchner', 'flat'),
    ('riesgo_pais', 'dia', date(2019, 12, 9), 872, '', 'JP Morgan (EMBI+), último día hábil del gobierno de Macri', 'flat'),
    ('riesgo_pais', 'dia', date(2019, 12, 11), 1467, '', 'JP Morgan (EMBI+), saltó en un solo día tras la asunción de Alberto Fernández', 'flat'),
    ('riesgo_pais', 'dia', date(2023, 12, 11), 1923, '', 'JP Morgan (EMBI+), asunción de Milei', 'flat'),

    # -- Alberto Fernández (10-dic-2019 a 10-dic-2023) -------------------
    # A diferencia de los puntos de transición de arriba (que sirven a DOS
    # gobiernos y por eso se duplican en 9/11-dic), estos son específicos
    # de la gestión de Alberto Fernández: se cargan una sola vez, fechados
    # el 11-dic-2019 (día siguiente a su asunción) o el 9-dic-2023 (último
    # día de su mandato), para no pisar los puntos de transición de
    # dólar/inflación/desempleo/riesgo país ya cargados arriba en esas
    # mismas fechas exactas. Son valores fijos — su mandato ya terminó, no
    # necesitan un comando que los mantenga actualizados (a pedido
    # explícito). Fuentes con reservas metodológicas quedan anotadas en el
    # propio delta_texto en vez de mostrarse como un dato sin matices;
    # donde no se encontró una cifra confiable (humor_social,
    # delitos_propiedad, percepcion_inseguridad, inversion_equipamiento,
    # confianza del consumidor/gobierno al inicio del mandato) se dejó
    # directamente sin cargar — sigue apareciendo "sin datos" en vez de
    # una estimación de baja confianza.
    ('dolar_blue', 'dia', date(2019, 12, 10), 69.50, '', 'cotización venta, cierre 10-dic-2019 — Ámbito Financiero', 'flat'),
    ('dolar_blue', 'dia', date(2023, 12, 8), 990, '', 'cotización venta, cierre 8-dic-2023 (10-dic fue domingo) — Ámbito Financiero', 'flat'),
    ('reservas_bcra', 'mes', date(2019, 12, 11), 12.08, '', 'estimación de consultoras — el BCRA no publica "reservas netas" oficialmente (Chequeado)', 'flat'),
    ('reservas_bcra', 'mes', date(2023, 12, 9), -11.50, '', 'estimación de consultoras, rango -10.000/-15.000 US$M según metodología (Chequeado)', 'flat'),
    ('resultado_fiscal', 'mes', date(2019, 12, 11), -0.44, '', 'resultado 2019 con ingresos extraordinarios (sin extraordinarios: -0,96%) — Ministerio de Economía', 'flat'),
    ('resultado_fiscal', 'mes', date(2023, 12, 9), -2.9, '', 'resultado 2023, incluye ingresos extraordinarios (sin 5G: -2,7%) — Ministerio de Economía', 'flat'),
    ('salario_real', 'mes', date(2019, 12, 11), -8.4, '', 'estimado a partir de nominal +40,9% vs. inflación +53,8% en 2019 — INDEC', 'flat'),
    ('salario_real', 'mes', date(2023, 12, 9), -19.6, '', 'estimado a partir de nominal +152,7% vs. inflación interanual +211,4% dic-2023 — INDEC', 'flat'),
    ('empleo_informal', 'mes', date(2023, 12, 9), 35.7, '', '4to trimestre 2023 — INDEC (EPH); no se encontró cifra confiable para dic-2019', 'flat'),
    ('canasta_basica', 'mes', date(2019, 12, 11), 38960.33, '', 'familia tipo, dic-2019 — INDEC', 'flat'),
    ('canasta_basica', 'mes', date(2023, 12, 9), 495798, '', 'familia tipo, dic-2023 — INDEC', 'flat'),
    ('tasa_pobreza', 'mes', date(2019, 12, 11), 35.5, '', '2do semestre 2019 — INDEC (EPH)', 'flat'),
    ('tasa_pobreza', 'mes', date(2023, 12, 9), 41.7, '', '2do semestre 2023 — INDEC (EPH)', 'flat'),
    ('tasa_indigencia', 'mes', date(2019, 12, 11), 8.0, '', '2do semestre 2019 — INDEC (EPH)', 'flat'),
    ('tasa_indigencia', 'mes', date(2023, 12, 9), 11.9, '', '2do semestre 2023 — INDEC (EPH)', 'flat'),
    ('gini', 'mes', date(2019, 12, 11), 0.439, '', '4to trimestre 2019 — INDEC (EPH)', 'flat'),
    ('gini', 'mes', date(2023, 12, 9), 0.435, '', '4to trimestre 2023 — INDEC (EPH)', 'flat'),
    ('brecha_ingresos', 'mes', date(2019, 12, 11), 16, '', 'decil 10/decil 1 (mediana), 4to trim. 2019 — INDEC (EPH)', 'flat'),
    ('brecha_ingresos', 'mes', date(2023, 12, 9), 13, '', 'decil 10/decil 1 (mediana), 4to trim. 2023 — INDEC (EPH)', 'flat'),
    ('ipi_manufacturero', 'mes', date(2019, 12, 11), 1.2, '', 'interanual, dic-2019 — INDEC', 'flat'),
    ('ipi_manufacturero', 'mes', date(2023, 12, 9), -12.8, '', 'interanual, dic-2023 — INDEC', 'flat'),
    ('capacidad_instalada', 'mes', date(2019, 12, 11), 56.9, '', 'dic-2019 — INDEC', 'flat'),
    ('capacidad_instalada', 'mes', date(2023, 12, 9), 54.9, '', 'dic-2023 — INDEC', 'flat'),
    ('produccion_agropecuaria', 'anio', date(2020, 6, 30), 97.6, '', 'campaña 2019/20: soja 49,6Mt + maíz 48,0Mt — Bolsa de Cereales de Buenos Aires', 'flat'),
    ('produccion_agropecuaria', 'anio', date(2024, 7, 11), 98.0, '', 'campaña 2023/24: soja 50,5Mt (BCBA) + maíz ~47,5Mt (BCR), leve discrepancia entre bolsas', 'flat'),
    ('cuenta_corriente', 'anio', date(2019, 12, 11), -0.9, '', 'déficit US$3.997M, año 2019 — BCRA/INDEC', 'flat'),
    ('cuenta_corriente', 'anio', date(2023, 12, 9), -3.4, '', 'déficit ~US$20.700M, año 2023 — INDEC', 'flat'),
    ('deuda_externa', 'mes', date(2019, 12, 11), 277.6, '', '4to trimestre 2019 — INDEC', 'flat'),
    ('deuda_externa', 'mes', date(2023, 12, 9), 286.0, '', '4to trimestre 2023 — INDEC', 'flat'),
    ('cpi_corrupcion', 'anio', date(2019, 12, 11), 45, '', 'Transparencia Internacional, edición 2019 (mismo valor ya atribuido al cierre de Macri)', 'flat'),
    ('cpi_corrupcion', 'anio', date(2023, 12, 9), 37, '', 'Transparencia Internacional, edición 2023, puesto 98/180 (publicada ene-2024, antes de la de Milei)', 'flat'),
    ('estado_derecho', 'anio', date(2019, 12, 11), 63, '', 'WJP Rule of Law Index 2019, de 126 países', 'flat'),
    ('estado_derecho', 'anio', date(2023, 12, 9), 63, '', 'WJP Rule of Law Index 2023, de 142 países (oct-2023)', 'flat'),
    ('gasto_publico', 'mes', date(2019, 12, 11), 43.5, '', 'año 2019 — Ministerio de Economía', 'flat'),
    ('gasto_publico', 'mes', date(2023, 12, 9), 41.9, '', 'año 2023 (una fuente cita 40,6%, posible revisión metodológica) — Ministerio de Economía', 'flat'),
    ('confianza_gobierno', 'mes', date(2019, 12, 11), 1.97, '', 'dic-2019, última medición de Macri — UTDT (ICG)', 'flat'),
    ('confianza_gobierno', 'mes', date(2023, 12, 9), 2.86, '', 'dic-2023, máximo de la serie, ya con efecto transición a Milei — UTDT (ICG)', 'flat'),
    ('esperanza_vida', 'anio', date(2019, 12, 11), 76.85, '', 'Banco Mundial, año 2019', 'flat'),
    ('esperanza_vida', 'anio', date(2023, 12, 9), 77.4, '', 'Banco Mundial, año 2023 (dato preliminar)', 'flat'),
    ('confianza_consumidor', 'mes', date(2023, 12, 9), 46, '', 'dic-2023, ya con efecto transición a Milei — UTDT (ICC)', 'flat'),
    ('expectativas_inflacion', 'mes', date(2019, 12, 11), 42.2, '', 'REM-BCRA, relevamiento dic-2019, a 12 meses', 'flat'),
    ('expectativas_inflacion', 'mes', date(2023, 12, 9), 213.0, '', 'REM-BCRA, relevamiento dic-2023, a 12 meses', 'flat'),
    ('aprobacion_gobierno', 'mes', date(2019, 12, 11), 49, '', 'aprueba (muy buena+buena) — D\'Alessio IROL/Berensztein, dic-2019', 'flat'),
    ('aprobacion_gobierno', 'mes', date(2023, 12, 9), 18, '', 'aprueba — Poliarquía, última semana de la gestión', 'flat'),
    ('acuerdo_fmi', 'mes', date(2019, 12, 11), None, 'Sin programa vigente (Stand-By 2018 discontinuado de facto)',
     'giros discontinuados desde ago-2019, tras las PASO', 'flat'),
    ('acuerdo_fmi', 'mes', date(2023, 12, 9), None, '7ª revisión del EFF acordada a nivel de staff',
     'aprobación formal del directorio recién el 31-ene-2024', 'flat'),
    ('calificacion_soberana', 'mes', date(2019, 12, 11), None, 'CCC-', 'perspectiva negativa — S&P Global Ratings', 'flat'),
    ('calificacion_soberana', 'mes', date(2023, 12, 9), None, 'CCC-', 'perspectiva negativa, sin cambios desde jun-2023 — S&P Global Ratings', 'flat'),
    ('swap_china', 'mes', date(2019, 12, 11), None, '~US$18.500-19.000 M de línea activa',
     'tramo efectivamente usado a esa fecha no precisado — BCRA', 'flat'),
    ('swap_china', 'mes', date(2023, 12, 9), None, 'US$5.000 M en uso (CNY 35.000 M)', 'tramo activado en jun-2023 — BCRA', 'flat'),
    ('mercosur_ue', 'mes', date(2019, 12, 11), None, 'Acuerdo político alcanzado (jun-2019)',
     'en revisión legal, pendiente de firma y ratificación — Mercosur/UE', 'flat'),
    ('mercosur_ue', 'mes', date(2023, 12, 9), None, 'Sin cerrar', 'la cumbre de dic-2023 no logró concluir la negociación', 'flat'),
    ('tasa_homicidios', 'anio', date(2019, 12, 11), 5.0, '', 'año 2019, mínimo desde 2001 — Ministerio de Seguridad (SNIC)', 'flat'),
    ('tasa_homicidios', 'anio', date(2023, 12, 9), 4.4, '', 'año 2023, 2.046 víctimas — Ministerio de Seguridad (SNIC)', 'flat'),
    ('tasa_encarcelamiento', 'anio', date(2019, 12, 11), 224, '', 'año 2019, sin comisarías (243 con comisarías) — SNEEP', 'flat'),
    ('tasa_encarcelamiento', 'anio', date(2022, 12, 31), 227, '', 'año 2022, último dato con tasa precisa disponible — SNEEP', 'flat'),
    ('ranking_poder_militar', 'anio', date(2020, 3, 1), 36, '', 'edición 2020 — Global Firepower Index', 'flat'),
    ('gasto_educativo', 'anio', date(2023, 12, 9), 1.34, '', 'solo Estado nacional, sin provincias — Argentinos por la Educación', 'flat'),
    ('tasa_analfabetismo', 'anio', date(2019, 12, 11), 1.9, '', 'Censo 2010, último dato disponible — el Censo 2022 no incluyó esta pregunta', 'flat'),

    # -- Mauricio Macri (10-dic-2015 a 10-dic-2019) ------------------------
    # Mismo criterio que la sección de Alberto Fernández de arriba: puntos
    # fechados el 11-dic-2015 (día siguiente a su asunción) o el 9-dic-2019
    # (último día de su mandato) para no pisar los puntos de transición
    # compartidos ya cargados en esas fechas exactas. Varios indicadores de
    # 2019 reutilizan EXACTAMENTE el mismo valor ya cargado para el inicio
    # de Alberto Fernández (mismo año, mismo dato real — dos investigaciones
    # separadas a veces encontraron cifras ligeramente distintas para el
    # mismo hecho según la fuente consultada; se prioriza una sola cifra
    # por consistencia en vez de cargar ambas). Donde no se encontró una
    # cifra confiable (humor_social, delitos_propiedad, percepcion_
    # inseguridad, ranking_poder_militar, tasa_escolarizacion, ipi_
    # manufacturero/canasta_basica/salario_real/confianza_consumidor/
    # expectativas_inflacion al inicio del mandato) se dejó sin cargar.
    ('reservas_bcra', 'mes', date(2015, 12, 10), 2.4, '', 'estimación de consultoras, rango 0-2,4 US$B según metodología — Analytica/PxQ', 'flat'),
    ('reservas_bcra', 'mes', date(2019, 12, 9), 11.5, '', 'estimación de consultoras, dic-2019 — Analytica/Outlier', 'flat'),
    ('resultado_fiscal', 'mes', date(2015, 12, 11), -5.4, '', 'año 2015, metodología original (revisada luego a -3,8% PBI) — Min. Hacienda', 'flat'),
    ('resultado_fiscal', 'mes', date(2019, 12, 9), -0.44, '', 'mismo resultado 2019 ya cargado para AF (sin extraordinarios: -0,96%)', 'flat'),
    ('salario_real', 'mes', date(2019, 12, 9), -8.4, '', 'mismo dato del año 2019 ya cargado para el inicio de AF — INDEC', 'flat'),
    ('empleo_informal', 'mes', date(2015, 12, 31), 33.4, '', '4to trim. 2015, INDEC advierte reservas metodológicas — emergencia estadística', 'flat'),
    ('empleo_informal', 'mes', date(2019, 12, 9), 31.5, '', 'promedio anual 2019, trimestre exacto no precisado — INDEC (EPH)', 'flat'),
    ('canasta_basica', 'mes', date(2019, 12, 9), 38960, '', 'mismo dato de dic-2019 ya cargado para el inicio de AF — INDEC', 'flat'),
    ('tasa_pobreza', 'mes', date(2016, 12, 31), 30.3, '', '2do semestre 2016, primer dato tras el corte de la serie 2013-2016 — INDEC', 'flat'),
    ('tasa_pobreza', 'mes', date(2019, 12, 9), 35.5, '', 'mismo dato de 2019 ya cargado para el inicio de AF — INDEC (EPH)', 'flat'),
    ('tasa_indigencia', 'mes', date(2016, 12, 31), 6.1, '', '2do semestre 2016, primer dato tras el corte de la serie — INDEC', 'flat'),
    ('tasa_indigencia', 'mes', date(2019, 12, 9), 8.0, '', 'mismo dato de 2019 ya cargado para el inicio de AF — INDEC (EPH)', 'flat'),
    ('gini', 'mes', date(2016, 12, 31), 0.428, '', '4to trim. 2016, dato más cercano tras el corte de la serie — INDEC (EPH)', 'flat'),
    ('gini', 'mes', date(2019, 12, 9), 0.439, '', 'mismo dato de 2019 ya cargado para el inicio de AF — INDEC (EPH)', 'flat'),
    ('brecha_ingresos', 'mes', date(2016, 12, 31), 14, '', 'decil 10/decil 1 (mediana), 4to trim. 2016, más cercano al corte — INDEC (EPH)', 'flat'),
    ('brecha_ingresos', 'mes', date(2019, 12, 9), 16, '', 'mismo dato de 2019 ya cargado para el inicio de AF — INDEC (EPH)', 'flat'),
    ('ipi_manufacturero', 'mes', date(2019, 12, 9), 1.2, '', 'mismo dato de dic-2019 ya cargado para el inicio de AF — INDEC', 'flat'),
    ('capacidad_instalada', 'mes', date(2015, 12, 11), 71.4, '', 'oct-2015, INDEC no publicó nov/dic-2015 por la emergencia estadística', 'flat'),
    ('capacidad_instalada', 'mes', date(2019, 12, 9), 56.9, '', 'mismo dato de dic-2019 ya cargado para el inicio de AF — INDEC', 'flat'),
    ('produccion_agropecuaria', 'anio', date(2016, 6, 30), 84.8, '', 'campaña 2015/16: soja ~55,3Mt + maíz ~29,5Mt — Bolsa de Cereales/Rosario', 'flat'),
    ('cuenta_corriente', 'anio', date(2015, 12, 11), -2.96, '', 'año 2015 — Banco Mundial (BN.CAB.XOKA.GD.ZS)', 'flat'),
    ('cuenta_corriente', 'anio', date(2019, 12, 9), -0.9, '', 'mismo dato de 2019 ya cargado para el inicio de AF — BCRA/INDEC', 'flat'),
    ('deuda_externa', 'mes', date(2015, 12, 11), 170.4, '', 'IV trimestre 2015 — BCRA/INDEC', 'flat'),
    ('deuda_externa', 'mes', date(2019, 12, 9), 277.6, '', 'mismo dato de dic-2019 ya cargado para el inicio de AF — INDEC', 'flat'),
    ('cpi_corrupcion', 'anio', date(2015, 12, 11), 32, '', 'Transparencia Internacional, edición 2015', 'flat'),
    ('estado_derecho', 'anio', date(2015, 12, 11), 51, '', 'edición 2016 (113 países), más cercana — la de 2015 no pudo confirmarse', 'flat'),
    ('estado_derecho', 'anio', date(2019, 12, 9), 63, '', 'mismo dato de la edición 2019 ya cargado para el inicio de AF — WJP', 'flat'),
    ('gasto_publico', 'mes', date(2015, 12, 11), 44.2, '', 'pico de la serie, año 2015 — Ministerio de Economía', 'flat'),
    ('gasto_publico', 'mes', date(2019, 12, 9), 43.5, '', 'mismo dato de 2019 ya cargado para el inicio de AF — Ministerio de Economía', 'flat'),
    ('confianza_gobierno', 'mes', date(2015, 12, 11), 1.80, '', 'última medición de CFK — UTDT (ICG)', 'flat'),
    ('confianza_gobierno', 'mes', date(2019, 12, 9), 1.97, '', 'última medición de Macri, +9% vs. dic-2015 — UTDT (ICG)', 'flat'),
    ('esperanza_vida', 'anio', date(2015, 12, 11), 76.6, '', 'año 2015 — Banco Mundial (SP.DYN.LE00.IN)', 'flat'),
    ('esperanza_vida', 'anio', date(2019, 12, 9), 76.85, '', 'mismo dato de 2019 ya cargado para el inicio de AF — Banco Mundial', 'flat'),
    ('cobertura_salud', 'anio', date(2015, 12, 11), 68, '', 'dato más cercano disponible (2014), 2015 no confirmado — INDEC (EPH)', 'flat'),
    ('cobertura_salud', 'anio', date(2019, 12, 9), 69.4, '', '1er trimestre 2019, obra social/prepaga/mutual — INDEC (EPH)', 'flat'),
    ('mortalidad_infantil', 'anio', date(2015, 12, 11), 9.7, '', 'año 2015 — DEIS, Ministerio de Salud', 'flat'),
    ('mortalidad_infantil', 'anio', date(2019, 12, 9), 9.2, '', 'año 2019, sube desde 8,8‰ en 2018 — DEIS, Ministerio de Salud', 'flat'),
    ('acceso_servicios', 'anio', date(2015, 12, 11), 53.8, '', 'cloacas, Censo 2010, mismo dato ya cargado en otros períodos — INDEC', 'flat'),
    ('acceso_servicios', 'anio', date(2019, 12, 9), 66.7, '', 'cloacas, 1er semestre 2019 — INDEC (EPH)', 'flat'),
    ('confianza_consumidor', 'mes', date(2015, 12, 11), 46.4, '', 'dic-2015 — UTDT (ICC)', 'flat'),
    ('expectativas_inflacion', 'mes', date(2019, 12, 9), 41.7, '', 'REM-BCRA, relevamiento dic-2019, a 12 meses', 'flat'),
    ('aprobacion_gobierno', 'mes', date(2015, 12, 11), 62.5, '', 'aprueba (muy buena+buena), 1ra encuesta post-asunción — Opinión Pública SyM', 'flat'),
    ('aprobacion_gobierno', 'mes', date(2019, 12, 9), 39, '', 'aprueba, encuestadora exacta no identificada con certeza — dic-2019', 'flat'),
    ('tasa_homicidios', 'anio', date(2015, 12, 11), 6.6, '', 'año 2015 — Ministerio de Seguridad (SNIC)', 'flat'),
    ('tasa_homicidios', 'anio', date(2019, 12, 9), 5.0, '', 'mismo dato de 2019 ya cargado para el inicio de AF — Min. Seguridad', 'flat'),
    ('tasa_encarcelamiento', 'anio', date(2015, 12, 11), 166, '', 'año 2015 — SNEEP', 'flat'),
    ('tasa_encarcelamiento', 'anio', date(2019, 12, 9), 224, '', 'mismo dato de 2019 ya cargado para el inicio de AF — SNEEP', 'flat'),
    ('gasto_defensa', 'anio', date(2015, 12, 11), 0.9, '', 'año 2015 — SIPRI Military Expenditure Database', 'flat'),
    ('gasto_defensa', 'anio', date(2019, 12, 9), 0.71, '', 'año 2019, valor más bajo en 60 años — SIPRI', 'flat'),
    ('inversion_equipamiento', 'anio', date(2019, 12, 9), 1.4, '', 'Bienes de Uso, % del presupuesto de Defensa, mínimo de la serie', 'flat'),
    ('resultados_pisa', 'anio', date(2018, 12, 1), 379, '', 'PISA 2018, edición más cercana a 2019 (es trienal) — OCDE, media=489', 'flat'),
    ('gasto_educativo', 'anio', date(2015, 12, 11), 1.59, '', 'Estado nacional, sin provincias, confianza moderada — Argentinos x la Educación', 'flat'),
    ('gasto_educativo', 'anio', date(2019, 12, 9), 1.08, '', 'Estado nacional, mínimo de la serie, confianza moderada — Argentinos x Educación', 'flat'),
    ('acuerdo_fmi', 'mes', date(2015, 12, 11), None, 'Sin programa vigente', 'sin acuerdo con el FMI desde 2004-2006', 'flat'),
    ('acuerdo_fmi', 'mes', date(2019, 12, 9), None, 'Stand-By Agreement (de facto discontinuado)',
     'giros discontinuados desde ago-2019, tras las PASO — SBA jun-2018', 'flat'),
    ('calificacion_soberana', 'mes', date(2015, 12, 11), None, 'CCC+', 'perspectiva estable — S&P Global Ratings', 'flat'),
    ('calificacion_soberana', 'mes', date(2019, 12, 9), None, 'CCC-', 'S&P Global Ratings, mismo valor ya cargado para el inicio de AF', 'flat'),
    ('swap_china', 'mes', date(2015, 12, 11), None, 'Swap por 70.000 M yuanes (2do acuerdo, 2014)',
     'segundo acuerdo (2014), ~US$3.100M convertidos a dic-2015 — BCRA', 'flat'),
    ('swap_china', 'mes', date(2019, 12, 9), None, '~US$18.500-19.000 M de línea activa',
     'mismo valor ya cargado para el inicio de AF (130.000M yuanes) — BCRA', 'flat'),
    ('mercosur_ue', 'mes', date(2015, 12, 11), None, 'En negociación, sin acuerdo',
     'negociaciones reanudadas 2013, sin cierre a dic-2015 — Mercosur/UE', 'flat'),
    ('mercosur_ue', 'mes', date(2019, 12, 9), None, 'Acuerdo político alcanzado (jun-2019)',
     'mismo valor ya cargado para el inicio de AF — Mercosur/UE', 'flat'),

    # -- Cristina Fernández de Kirchner, 1er y 2do mandato ------------------
    # CFK1: 10-dic-2007 a 10-dic-2011. CFK2: 10-dic-2011 a 10-dic-2015 —
    # dos gobiernos separados en el modelo (misma persona, reelección), así
    # que se cargan como tal. A diferencia de las secciones anteriores, acá
    # el límite entre CFK1 y CFK2 es el mismo día para la misma persona (no
    # hay "entrante" ni "saliente" distintos) así que un solo punto fechado
    # 10-dic-2011 sirve de cierre de CFK1 e inicio de CFK2 sin necesidad de
    # duplicarlo en 9/11-dic. El límite CFK2/Macri sí es una transición de
    # persona — sigue el mismo criterio 9/11-dic que el resto del archivo,
    # y varios valores de dic-2015 reutilizan el mismo dato ya cargado para
    # el inicio de Macri más arriba, por la razón ya explicada ahí.
    # Esta es la era de mayor incertidumbre de datos del sitio: el INDEC
    # estuvo intervenido/cuestionado 2007-2015 (inflación y pobreza son los
    # casos más conocidos), varias series recién arrancaron después (REM
    # del BCRA en 2016, WJP Rule of Law Index con cobertura confiable desde
    # 2015, Global Firepower sin archivo histórico público) y varias otras
    # quedaron discontinuadas en el corte 2013-2016 (pobreza/indigencia).
    # Donde la investigación no encontró una cifra confiable o encontró
    # cifras contradictorias entre fuentes sin forma de resolverlas
    # (salario_real, canasta_basica, brecha_ingresos, delitos_propiedad,
    # percepcion_inseguridad, humor_social, expectativas_inflacion,
    # inversion_equipamiento, ranking_poder_militar, calificacion_soberana
    # 2007/2011, confianza_gobierno 2007/2011, cobertura_salud 2007/2011,
    # gasto_publico 2007/2011, estado_derecho, efectivos_ffaa 2007/2011,
    # gasto_defensa 2007/2011) se dejó sin cargar en vez de forzar un dato.
    ('reservas_bcra', 'mes', date(2007, 12, 11), 45.6, '', 'reservas brutas (no hay serie de netas para esta época) — Chequeado', 'flat'),
    ('reservas_bcra', 'mes', date(2011, 12, 10), 46.376, '', 'reservas brutas — BCRA, Informe Monetario Mensual dic-2011', 'flat'),
    ('reservas_bcra', 'mes', date(2015, 12, 9), 25.6, '', 'reservas brutas, aprox. 10-dic-2015 — Chequeado', 'flat'),
    ('resultado_fiscal', 'mes', date(2007, 12, 11), 2.9, '', 'superávit primario, año 2007 — Chequeado', 'flat'),
    ('resultado_fiscal', 'mes', date(2011, 12, 10), 0.2, '', 'superávit primario, año 2011, último año antes del déficit — Chequeado', 'flat'),
    ('resultado_fiscal', 'mes', date(2015, 12, 9), -5.4, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — Min. Hacienda', 'flat'),
    ('empleo_informal', 'mes', date(2015, 3, 31), 31.9, '', '1er trimestre 2015, coincide con cambio metodológico EPH — INDEC', 'flat'),
    ('tasa_pobreza', 'mes', date(2011, 12, 10), 6.5, '', '2do semestre 2011, cifra oficial cuestionada como subestimada — INDEC', 'flat'),
    ('tasa_indigencia', 'mes', date(2011, 12, 10), 1.7, '', '2do semestre 2011, cifra oficial cuestionada como subestimada — INDEC', 'flat'),
    ('gini', 'mes', date(2011, 12, 10), 0.394, '', '3er trimestre 2011, dato más cercano — INDEC (EPH)', 'flat'),
    ('ipi_manufacturero', 'mes', date(2007, 12, 11), 9.5, '', 'EMI-INDEC, dic-2007 (con estacionalidad)', 'flat'),
    ('ipi_manufacturero', 'mes', date(2011, 12, 10), 2.2, '', 'EMI-INDEC, dic-2011 (con estacionalidad)', 'flat'),
    ('capacidad_instalada', 'mes', date(2007, 12, 11), 74.5, '', 'INDEC, dic-2007', 'flat'),
    ('capacidad_instalada', 'mes', date(2011, 12, 10), 82.0, '', 'INDEC, dic-2011', 'flat'),
    ('capacidad_instalada', 'mes', date(2015, 12, 9), 71.4, '', 'mismo dato de oct-2015 ya cargado para el inicio de Macri — INDEC', 'flat'),
    ('produccion_agropecuaria', 'anio', date(2008, 5, 31), 67.35, '', 'campaña 2007/08: soja 47,2Mt + maíz 20,2Mt — Bolsa de Comercio de Rosario', 'flat'),
    ('produccion_agropecuaria', 'anio', date(2012, 5, 31), 59.9, '', 'campaña 2011/12: soja 40,9Mt + maíz 19,0Mt — Bolsa de Comercio de Rosario', 'flat'),
    ('produccion_agropecuaria', 'anio', date(2015, 5, 31), 81.6, '', 'campaña 2014/15: soja 58Mt + maíz 23,6Mt — Bolsa de Comercio de Rosario', 'flat'),
    ('balanza_comercial', 'mes', date(2007, 12, 11), 1786, '', 'superávit, dic-2007 — INDEC (Intercambio Comercial Argentino)', 'flat'),
    ('balanza_comercial', 'mes', date(2011, 12, 10), 280, '', 'superávit, dic-2011, dato preliminar — INDEC (ICA)', 'flat'),
    ('balanza_comercial', 'mes', date(2015, 12, 9), -1110, '', 'déficit, dic-2015, peor mes del año — INDEC (ICA)', 'flat'),
    ('exportaciones', 'mes', date(2007, 12, 11), 5668, '', 'dic-2007 — INDEC (ICA)', 'flat'),
    ('exportaciones', 'mes', date(2011, 12, 10), 6269, '', 'dic-2011, dato preliminar — INDEC (ICA)', 'flat'),
    ('exportaciones', 'mes', date(2015, 12, 9), 3411, '', 'dic-2015 — INDEC (ICA)', 'flat'),
    ('cuenta_corriente', 'anio', date(2007, 12, 11), 2.10, '', 'año 2007 — Banco Mundial (BN.CAB.XOKA.GD.ZS)', 'flat'),
    ('cuenta_corriente', 'anio', date(2011, 12, 10), -1.01, '', 'año 2011 — Banco Mundial (BN.CAB.XOKA.GD.ZS)', 'flat'),
    ('cuenta_corriente', 'anio', date(2015, 12, 9), -2.96, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — Banco Mundial', 'flat'),
    ('deuda_externa', 'mes', date(2007, 12, 11), 120.8, '', 'fin de 2007 — Banco Mundial (stock anual, no trimestral BCRA)', 'flat'),
    ('deuda_externa', 'mes', date(2011, 12, 10), 142.9, '', 'fin de 2011 — Banco Mundial (BCRA reportó 136,4B a 3er trim.)', 'flat'),
    ('deuda_externa', 'mes', date(2015, 12, 9), 170.4, '', 'mismo dato de dic-2015 ya cargado para el inicio de Macri — INDEC', 'flat'),
    ('cpi_corrupcion', 'anio', date(2007, 12, 11), 29, '', 'Transparencia Internacional 2007, escala vieja 2,9/10, puesto 105/180', 'flat'),
    ('cpi_corrupcion', 'anio', date(2011, 12, 10), 30, '', 'Transparencia Internacional 2011, última ed. escala 0-10, puesto 100/183', 'flat'),
    ('gasto_publico', 'mes', date(2015, 12, 9), 44.2, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — Min. Economía', 'flat'),
    ('confianza_gobierno', 'mes', date(2015, 12, 9), 1.80, '', 'última medición de CFK, mismo dato ya cargado para Macri — UTDT (ICG)', 'flat'),
    ('esperanza_vida', 'anio', date(2007, 12, 11), 74.78, '', 'año 2007 — Banco Mundial (SP.DYN.LE00.IN)', 'flat'),
    ('esperanza_vida', 'anio', date(2011, 12, 10), 76.1, '', 'año 2011 — Banco Mundial (SP.DYN.LE00.IN)', 'flat'),
    ('esperanza_vida', 'anio', date(2015, 12, 9), 76.6, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — Banco Mundial', 'flat'),
    ('cobertura_salud', 'anio', date(2015, 12, 9), 68, '', 'mismo dato (2014, más cercano) ya cargado para el inicio de Macri', 'flat'),
    ('mortalidad_infantil', 'anio', date(2007, 12, 11), 13.3, '', 'año 2007 — DEIS, Ministerio de Salud', 'flat'),
    ('mortalidad_infantil', 'anio', date(2011, 12, 10), 11.7, '', 'año 2011 — DEIS, Ministerio de Salud', 'flat'),
    ('mortalidad_infantil', 'anio', date(2015, 12, 9), 9.7, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — DEIS', 'flat'),
    ('confianza_consumidor', 'mes', date(2011, 12, 10), 46.4, '', 'dic-2011, subió 8,7% en el mes — UTDT (ICC)', 'flat'),
    ('aprobacion_gobierno', 'mes', date(2007, 12, 11), 56, '', 'imagen positiva, recién asumida — Poliarquía, dic-2007', 'flat'),
    ('aprobacion_gobierno', 'mes', date(2011, 12, 10), 69, '', 'aprobación de gestión — Poliarquía, dic-2011', 'flat'),
    ('tasa_homicidios', 'anio', date(2007, 12, 11), 5.0, '', 'año 2007, dato de fuente agregada, baja precisión — SNIC', 'flat'),
    ('tasa_homicidios', 'anio', date(2015, 12, 9), 6.6, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — Min. Seguridad', 'flat'),
    ('tasa_encarcelamiento', 'anio', date(2011, 12, 10), 123, '', '2011, dato de fuente agregada sin PDF primario confirmado — SNEEP', 'flat'),
    ('tasa_encarcelamiento', 'anio', date(2015, 12, 9), 166, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — SNEEP', 'flat'),
    ('gasto_defensa', 'anio', date(2015, 12, 9), 0.9, '', 'mismo dato de 2015 ya cargado para el inicio de Macri — SIPRI', 'flat'),
    ('gasto_educativo', 'anio', date(2015, 12, 9), 1.59, '', 'mismo dato de 2015 ya cargado para el inicio de Macri', 'flat'),
    ('resultados_pisa', 'anio', date(2007, 12, 11), 381, '', 'edición 2006, la más cercana a dic-2007 — OCDE', 'flat'),
    ('resultados_pisa', 'anio', date(2011, 12, 10), 388, '', 'edición 2009, la más cercana conocida a dic-2011 — OCDE', 'flat'),
    ('resultados_pisa', 'anio', date(2015, 12, 9), 388, '', 'edición 2012, la más cercana conocida a dic-2015 — OCDE, puesto 59/65', 'flat'),
    ('tasa_escolarizacion', 'anio', date(2010, 10, 27), 97.6, '', 'Censo 2010, único dato censal disponible — INDEC', 'flat'),
    ('tasa_escolarizacion', 'anio', date(2011, 12, 10), 97.6, '', 'carry-forward del Censo 2010, único dato disponible — INDEC', 'flat'),
    ('acuerdo_fmi', 'mes', date(2007, 12, 11), None, 'Sin programa vigente', 'sin acuerdo con el FMI desde 2004-2006', 'flat'),
    ('acuerdo_fmi', 'mes', date(2011, 12, 10), None, 'Sin programa vigente', 'confirmado sin programa vigente — FMI', 'flat'),
    ('acuerdo_fmi', 'mes', date(2015, 12, 9), None, 'Sin programa vigente',
     'mismo dato ya cargado para el inicio de Macri', 'flat'),
    ('calificacion_soberana', 'mes', date(2015, 12, 9), None, 'CCC+',
     'mismo valor ya cargado para el inicio de Macri — S&P Global Ratings', 'flat'),
    ('swap_china', 'mes', date(2007, 12, 11), None, 'No existía swap con China',
     'el primer swap se firmó recién en 2009', 'flat'),
    ('swap_china', 'mes', date(2011, 12, 10), None, 'Swap 2009 vigente (RMB 70.000 M), nunca activado',
     'acuerdo de 2009, según fuentes nunca activado antes de 2014 — BCRA', 'flat'),
    ('swap_china', 'mes', date(2015, 12, 9), None, 'Swap por 70.000 M yuanes (2do acuerdo, 2014)',
     'mismo valor ya cargado para el inicio de Macri — BCRA', 'flat'),
    ('mercosur_ue', 'mes', date(2007, 12, 11), None, 'Negociaciones estancadas, sin acuerdo',
     'negociaciones estancadas desde 2004', 'flat'),
    ('mercosur_ue', 'mes', date(2011, 12, 10), None, 'Negociaciones reanudadas, en curso',
     'reanudadas en 2010, 4ta ronda en curso — Comisión Europea', 'flat'),
    ('mercosur_ue', 'mes', date(2015, 12, 9), None, 'En negociación, sin acuerdo',
     'mismo valor ya cargado para el inicio de Macri — Mercosur/UE', 'flat'),
    ('acceso_servicios', 'anio', date(2015, 12, 9), 53.8, '', 'cloacas, Censo 2010, carry-forward, único dato disponible — INDEC', 'flat'),
    ('tasa_analfabetismo', 'anio', date(2015, 12, 9), 1.9, '', 'Censo 2010, carry-forward, único dato disponible — INDEC', 'flat'),
]


class Command(BaseCommand):
    help = 'Carga puntos reales sueltos (verificados por búsqueda web) para indicadores sin fuente automática.'

    def handle(self, *args, **options):
        objetos = []
        ids_tocados = set()
        ids_inexistentes = set()

        for ind_id, gran, fecha, valor, valor_texto, delta_texto, trend in PUNTOS:
            if not Indicador.objects.filter(id=ind_id).exists():
                ids_inexistentes.add(ind_id)
                continue
            objetos.append(IndicadorValor(
                indicador_id=ind_id, fecha=fecha, granularidad=gran,
                valor_numerico=valor, valor_texto=valor_texto,
                delta_texto=delta_texto, trend=trend,
            ))
            ids_tocados.add(ind_id)

        IndicadorValor.objects.bulk_create(
            objetos,
            update_conflicts=True,
            unique_fields=['indicador', 'fecha', 'granularidad'],
            update_fields=['valor_numerico', 'valor_texto', 'delta_texto', 'trend'],
            batch_size=200,
        )

        for ind_id in ids_inexistentes:
            self.stdout.write(self.style.WARNING(f'{ind_id}: no existe en la base, se salta (¿corriste seed_pulso_austral?).'))
        self.stdout.write(self.style.SUCCESS(
            f'{len(objetos)} puntos reales cargados para {len(ids_tocados)} indicadores.'
        ))
