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
    ('salario_real', 'mes', date(2026, 4, 1), 1.1, '', 'interanual, empleo registrado privado — Min. Capital Humano/INDEC', 'up'),
    ('empleo_informal', 'mes', date(2025, 1, 1), 42.0, '', '1er trimestre — INDEC (EPH)', 'flat'),
    ('empleo_informal', 'mes', date(2025, 10, 1), 43.0, '', '4to trimestre', 'up'),
    ('empleo_informal', 'mes', date(2026, 1, 1), 44.2, '', '1er trimestre, +2,2pp interanual — INDEC (EPH)', 'up'),
    ('canasta_basica', 'mes', date(2025, 6, 1), 1128398, '', 'familia tipo — INDEC', 'flat'),
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
