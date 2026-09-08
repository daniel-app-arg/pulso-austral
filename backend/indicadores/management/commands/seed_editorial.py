"""
Seed de contenido editorial: el directorio de medios de comunicación (con
su caracterización de orientación) y los períodos de gobierno (para poder
resumir todos los indicadores por mandato).

Sobre el directorio de medios: es una clasificación de referencia, no una
medición objetiva — mismo espíritu que los "media bias charts" de sitios
como AllSides o Ad Fontes Media, adaptado a medios argentinos. Cada
`descripcion` explica de dónde sale la caracterización (línea editorial
histórica, pertenencia a un grupo, etc.) para que quede claro que es una
apreciación y no una sentencia. Pensado para revisarse y ajustarse a mano
desde el admin — el criterio final es del sitio, no de este seed.

Uso:
    python manage.py seed_editorial
"""

from datetime import date

from django.core.management.base import BaseCommand

from indicadores.models import Gobierno, Indicador, Medio

MEDIOS = [
    ('clarin', 'Clarín', 'https://www.clarin.com/', 'diario', 'centro_derecha',
     'El diario de mayor tirada del país, del multimedios Grupo Clarín. Se lo '
     'describe habitualmente como centro-derecha, con una relación históricamente '
     'tensa con los gobiernos kirchneristas (Ley de Medios, conflicto por Papel '
     'Prensa) y más cercana a gobiernos de signo liberal o de centro-derecha.'),
    ('la-nacion', 'La Nación', 'https://www.lanacion.com.ar/', 'diario', 'centro_derecha',
     'Fundado en 1870 por Bartolomé Mitre, mantiene una línea editorial '
     'liberal-conservadora. Suele adoptar posiciones críticas del intervencionismo '
     'estatal y es percibido como cercano a sectores empresariales y agropecuarios.'),
    ('pagina12', 'Página/12', 'https://www.pagina12.com.ar/', 'diario', 'centro_izquierda',
     'Fundado en 1987, se identifica históricamente con el progresismo y el '
     'kirchnerismo; su cobertura suele ser favorable a gobiernos peronistas de ese '
     'signo y crítica de las políticas de ajuste fiscal.'),
    ('infobae', 'Infobae', 'https://www.infobae.com/', 'diario', 'centro',
     'Medio digital de alcance masivo, uno de los más leídos en español. Su '
     'cobertura política es percibida como más plural que la de los diarios '
     'tradicionales, aunque en temas económicos suele describirse más cercana al '
     'centro y centro-derecha.'),
    ('perfil', 'Perfil', 'https://www.perfil.com/', 'revista', 'centro',
     'Dirigido por Jorge Fontevecchia, se presenta como independiente y plural, '
     'con columnistas de espectro amplio; se lo suele describir como centrista '
     'con matices liberales.'),
    ('ambito-financiero', 'Ámbito Financiero', 'https://www.ambito.com/', 'diario', 'centro_derecha',
     'Medio especializado en economía y mercados. Prioriza el análisis financiero '
     'por sobre la agenda política partidaria, aunque su línea en temas económicos '
     'es habitualmente favorable a políticas de mercado.'),
    ('el-cronista', 'El Cronista Comercial', 'https://www.cronista.com/', 'diario', 'centro_derecha',
     'Diario económico con una línea editorial favorable a políticas de mercado y '
     'ortodoxia fiscal; su cobertura política suele ser más afín a gobiernos con '
     'esa orientación.'),
    ('tn', 'TN (Todo Noticias)', 'https://tn.com.ar/', 'tv', 'centro_derecha',
     'Canal de noticias de 24 horas del Grupo Clarín; comparte en líneas generales '
     'la orientación editorial del diario Clarín.'),
    ('c5n', 'C5N', 'https://www.c5n.com/', 'tv', 'centro_izquierda',
     'Canal de noticias del Grupo Indalo/América. Su cobertura es percibida como '
     'cercana al kirchnerismo y a organizaciones sindicales, con una agenda '
     'habitualmente crítica de gobiernos de centro-derecha.'),
    ('a24', 'A24', 'https://www.a24.com/', 'tv', 'centro_derecha',
     'Canal de noticias del Grupo América. Su cobertura política suele describirse '
     'como más cercana a posiciones de centro-derecha, con panelistas de esa órbita.'),
    ('la-izquierda-diario', 'La Izquierda Diario', 'https://www.laizquierdadiario.com/', 'diario', 'izquierda',
     'Medio digital vinculado al Partido de Trabajadores Socialistas (PTS-FIT). Se '
     'define explícitamente como de izquierda socialista y trotskista.'),
    ('tiempo-argentino', 'Tiempo Argentino', 'https://www.tiempoar.com.ar/', 'diario', 'centro_izquierda',
     'Diario cooperativo con una línea editorial identificada con el progresismo y '
     'sectores sindicales; históricamente cercano al kirchnerismo.'),
    ('chequeado', 'Chequeado', 'https://chequeado.com/', 'factchecking', 'centro',
     'Organización dedicada exclusivamente a la verificación de discursos y datos '
     'públicos, sin línea editorial partidaria — se incluye como referencia de '
     'fact-checking, no de opinión.'),
    ('radio-mitre', 'Radio Mitre', 'https://radiomitre.cienradios.com/', 'radio', 'centro_derecha',
     'Radio de noticias del Grupo Clarín; comparte la orientación editorial general '
     'del multimedios.'),
]

# Mandatos presidenciales desde el retorno a mandatos de 4 años (reforma
# constitucional de 1994). fecha_fin=None significa "en curso".
GOBIERNOS = [
    ('nestor-kirchner', 'Néstor Kirchner', 'Frente para la Victoria', date(2003, 5, 25), date(2007, 12, 10)),
    ('cfk-1', 'Cristina Fernández de Kirchner (1er mandato)', 'Frente para la Victoria', date(2007, 12, 10), date(2011, 12, 10)),
    ('cfk-2', 'Cristina Fernández de Kirchner (2do mandato)', 'Frente para la Victoria', date(2011, 12, 10), date(2015, 12, 10)),
    ('macri', 'Mauricio Macri', 'Cambiemos', date(2015, 12, 10), date(2019, 12, 10)),
    ('alberto-fernandez', 'Alberto Fernández', 'Frente de Todos', date(2019, 12, 10), date(2023, 12, 10)),
    ('milei', 'Javier Milei', 'La Libertad Avanza', date(2023, 12, 10), None),
]

# Glosario: cómo se mide/calcula cada indicador — para la sección
# /glosario del sitio. No hace falta cubrir los 47: los que falten
# simplemente no muestran metodología ahí (mejor vacío que inventado).
METODOLOGIAS = {
    # macro
    'dolar_oficial': 'Tipo de cambio minorista promedio (Comunicación A del BCRA): promedio de las cotizaciones de venta relevadas en bancos y casas de cambio.',
    'dolar_blue': 'Cotización de referencia del mercado paralelo/informal, relevada por medios especializados a partir de operadores del mercado — no tiene una fuente oficial única.',
    'merval': 'Índice bursátil de las principales acciones que cotizan en Byma (Bolsa de Comercio de Buenos Aires), ponderado por capitalización y liquidez.',
    'inflacion_interanual': 'Variación del Índice de Precios al Consumidor (IPC) respecto al mismo mes del año anterior — INDEC, sobre una canasta representativa de bienes y servicios.',
    'riesgo_pais': 'EMBI+ Argentina (J.P. Morgan): diferencial de tasa entre bonos soberanos argentinos y bonos del Tesoro de EE.UU. de plazo comparable, en puntos básicos.',
    'reservas_bcra': 'Activos externos líquidos en poder del Banco Central (oro, divisas, DEGs, posición en organismos internacionales), publicados diariamente.',
    'resultado_fiscal': 'Ingresos menos gastos primarios (sin contar intereses de deuda) del Sector Público Nacional no Financiero, como % del PBI.',
    # empleo
    'desempleo': 'Tasa de desocupación de la Encuesta Permanente de Hogares (EPH, INDEC): población desocupada sobre población económicamente activa, en los aglomerados urbanos relevados.',
    'salario_real': 'Variación del salario nominal (índice de salarios INDEC) descontando la inflación del mismo período.',
    'empleo_informal': 'Porcentaje de asalariados sin descuento jubilatorio sobre el total de asalariados — EPH, INDEC.',
    'canasta_basica': 'Valor de la Canasta Básica Total (CBT) para un hogar tipo — INDEC. Es también el umbral que define la línea de pobreza.',
    # pobreza
    'tasa_pobreza': 'Porcentaje de personas cuyo ingreso familiar no alcanza el valor de la Canasta Básica Total — EPH, INDEC, medición semestral.',
    'tasa_indigencia': 'Porcentaje de personas cuyo ingreso no alcanza el valor de la Canasta Básica Alimentaria (línea de indigencia) — EPH, INDEC.',
    'gini': 'Coeficiente de Gini de la distribución del ingreso per cápita familiar: 0 es igualdad perfecta, 1 es desigualdad máxima.',
    'brecha_ingresos': 'Cociente entre el ingreso promedio del 10% más rico y el del 10% más pobre de la distribución de ingresos.',
    # produccion
    'emae': 'Estimador Mensual de Actividad Económica (INDEC): proxy mensual del PBI, variación interanual del índice de volumen físico agregado de la economía.',
    'ipi_manufacturero': 'Índice de Producción Industrial manufacturero (INDEC): variación interanual del volumen físico producido por la industria.',
    'capacidad_instalada': 'Porcentaje de la capacidad productiva instalada que efectivamente se usa, relevado por INDEC en un panel de grandes empresas industriales.',
    'produccion_agropecuaria': 'Toneladas totales de la cosecha gruesa (soja y maíz, principalmente), según estimaciones de las bolsas de cereales.',
    # sector_externo
    'balanza_comercial': 'Diferencia entre exportaciones e importaciones de bienes (valor FOB), en millones de dólares mensuales — INDEC.',
    'cuenta_corriente': 'Saldo de la cuenta corriente del balance de pagos (comercio de bienes y servicios, rentas, transferencias) como % del PBI — BCRA.',
    'deuda_externa': 'Stock de deuda bruta con acreedores del exterior, sector público y privado, en miles de millones de dólares.',
    'exportaciones': 'Valor FOB total de bienes exportados por mes, en millones de dólares — INDEC.',
    # institucional
    'cpi_corrupcion': 'Índice de Percepción de la Corrupción (Transparencia Internacional): encuesta a expertos y empresarios sobre corrupción en el sector público, de 0 (muy corrupto) a 100 (muy transparente).',
    'estado_derecho': 'Posición de Argentina en el Rule of Law Index (World Justice Project): ranking global armado con encuestas a hogares y expertos sobre 8 factores (límites al poder, ausencia de corrupción, derechos fundamentales, etc.) — cuanto más bajo el número, mejor.',
    'gasto_publico': 'Gasto público consolidado (nación + provincias + municipios) como % del PBI.',
    'confianza_gobierno': 'Índice de Confianza en el Gobierno (UTDT): encuesta mensual sobre la evaluación de la gestión en 5 dimensiones, escala de 0 a 5.',
    # bienestar
    'esperanza_vida': 'Años de vida esperados al nacer, estimados a partir de tablas de mortalidad — INDEC/Naciones Unidas.',
    'cobertura_salud': 'Porcentaje de la población con cobertura de salud (obra social, prepaga o programa público específico) más allá del sistema público general — INDEC.',
    'mortalidad_infantil': 'Muertes de menores de 1 año cada 1.000 nacidos vivos — estadísticas vitales, Ministerio de Salud.',
    'acceso_servicios': 'Porcentaje de hogares con acceso a red de agua potable y cloacas — INDEC (censo/EPH).',
    # percepcion
    'confianza_consumidor': 'Índice de Confianza del Consumidor (UTDT): encuesta mensual sobre la percepción de la situación personal y macroeconómica, de 0 a 100.',
    'expectativas_inflacion': 'Mediana de las proyecciones de inflación a 12 meses del Relevamiento de Expectativas de Mercado (REM) del BCRA — encuesta a consultoras y bancos.',
    'humor_social': 'Porcentaje de personas que se declara optimista sobre la situación económica del país, según encuestadoras privadas relevadas por medios especializados.',
    'aprobacion_gobierno': 'Porcentaje que aprueba la gestión de gobierno — encuestas de opinión pública, distintas encuestadoras según el mes.',
    # geo (cualitativos)
    'acuerdo_fmi': 'Estado del programa vigente con el FMI (revisión de metas, desembolsos), en base a comunicados oficiales del organismo y del gobierno.',
    'calificacion_soberana': 'Calificación crediticia de la deuda soberana en moneda extranjera asignada por una agencia calificadora (S&P Global Ratings).',
    'swap_china': 'Monto activo del swap de monedas entre el BCRA y el Banco Popular de China.',
    'mercosur_ue': 'Estado del acuerdo de asociación birregional entre el Mercosur y la Unión Europea.',
    # seguridad
    'tasa_homicidios': 'Homicidios dolosos cada 100.000 habitantes por año — Ministerio de Seguridad, Sistema Nacional de Información Criminal.',
    'delitos_propiedad': 'Variación interanual de delitos contra la propiedad (robos, hurtos) registrados por las fuerzas de seguridad.',
    'tasa_encarcelamiento': 'Personas privadas de la libertad cada 100.000 habitantes — Sistema Nacional de Estadísticas sobre Ejecución de la Pena (SNEEP).',
    'percepcion_inseguridad': '"Termómetro" de riesgo delictivo percibido, de 0 a 10 — Monitor de Inseguridad, Observatorio de Psicología Social Aplicada (OPSA-UBA).',
    # desarrollo_militar
    'gasto_defensa': 'Gasto en defensa como % del PBI — base de datos de gasto militar de SIPRI (Stockholm International Peace Research Institute).',
    'efectivos_ffaa': 'Personal militar activo (Ejército, Armada, Fuerza Aérea), en miles — Ministerio de Defensa.',
    'inversion_equipamiento': 'Porcentaje del presupuesto de defensa destinado a inversión en equipamiento y modernización, en vez de gastos corrientes.',
    'ranking_poder_militar': 'Posición de Argentina en el ranking de poder militar convencional de Global Firepower — cuanto más bajo el número, mayor poder relativo estimado.',
    # educacion
    'resultados_pisa': 'Puntaje de Argentina en la prueba de Matemática del Programa Internacional de Evaluación de Estudiantes (PISA, OCDE), aplicada cada 3 años a alumnos de 15 años.',
    'gasto_educativo': 'Inversión educativa del Estado nacional (no incluye provincias) como % del PBI, según la Ley de Financiamiento Educativo — Argentinos por la Educación, en base a datos del Ministerio de Economía.',
    'tasa_escolarizacion': 'Porcentaje de niños, niñas y adolescentes de 4 a 17 años que asisten a un establecimiento educativo formal — INDEC (EPH/Censo).',
    'tasa_analfabetismo': 'Porcentaje de la población de 10 años o más que no sabe leer ni escribir — INDEC (Censo Nacional de Población).',
}


class Command(BaseCommand):
    help = 'Carga el directorio de medios de comunicación, los períodos de gobierno y el glosario de metodología.'

    def handle(self, *args, **options):
        for i, (medio_id, nombre, url, tipo, orientacion, descripcion) in enumerate(MEDIOS):
            Medio.objects.update_or_create(
                id=medio_id,
                defaults={
                    'nombre': nombre, 'url': url, 'tipo': tipo,
                    'orientacion': orientacion, 'descripcion': descripcion, 'orden': i,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(MEDIOS)} medios OK.'))

        for i, (gob_id, presidente, partido, inicio, fin) in enumerate(GOBIERNOS):
            Gobierno.objects.update_or_create(
                id=gob_id,
                defaults={
                    'presidente': presidente, 'partido': partido,
                    'fecha_inicio': inicio, 'fecha_fin': fin, 'orden': i,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'{len(GOBIERNOS)} gobiernos OK.'))

        actualizados = 0
        for indicador_id, texto in METODOLOGIAS.items():
            actualizados += Indicador.objects.filter(id=indicador_id).update(metodologia=texto)
        self.stdout.write(self.style.SUCCESS(f'{actualizados} metodologías de indicadores OK.'))
