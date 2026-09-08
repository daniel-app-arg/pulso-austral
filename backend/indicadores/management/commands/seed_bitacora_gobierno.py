"""
Carga una selección curada de la "Bitácora de gestión" del Gobierno
Nacional (argentina.gob.ar/bitacora) como Noticias y como eventos de la
Línea de tiempo.

OJO — esto NO es periodismo independiente: es contenido autopublicado
por el propio Poder Ejecutivo sobre su propia gestión, sin cobertura de
hechos negativos ni contrapunto. Se carga con `medio_id='presidencia-
nacion'` (ver seed_editorial.py), que deja explícito en su `descripcion`
que es una fuente oficial, no editorial.

La bitácora completa filtrada en "Destacados" tiene ~146 entradas desde
diciembre de 2023 hasta hoy — muchas más que las 26 noticias
independientes ya cargadas en seed_noticias_reales.py (curadas de medios
de todo el espectro político, con cobertura tanto favorable como crítica
del gobierno de turno). Cargar las 146 hubiera desbalanceado fuertemente
el mix editorial del sitio, así que esto es una selección de ~35 hitos
genuinamente significativos (leyes sancionadas, privatizaciones
completadas, hitos fiscales/macro, anuncios diplomáticos concretos) —
se excluyen los anuncios menores y, sobre todo, las ~25 entradas
mensuales repetitivas de "Índice de inflación [mes]: X%" (ya redundantes
con el indicador `inflacion_interanual` del propio sitio, con datos
reales).

Las fechas de la bitácora solo tienen precisión de mes (no de día) — se
usa el día 15 de cada mes como convención neutral, no como un dato real.

`sentimiento` se carga como 'neutral' para todos los eventos: son hechos
reportados por una fuente interesada, no una evaluación editorial propia
del sitio (a diferencia de los otros eventos de TIMELINE en
seed_pulso_austral.py, con fuentes independientes, donde sí se asigna
positivo/negativo/neutral como juicio editorial).

Uso:
    python manage.py seed_bitacora_gobierno
"""

from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from indicadores.models import EventoTimeline, Noticia

MEDIO_ID = 'presidencia-nacion'
URL_BITACORA = 'https://www.argentina.gob.ar/bitacora'

# (categoria_id, fecha, kicker, titulo, bajada)
ENTRADAS = [
    ('geo', date(2024, 1, 15), 'Relaciones Exteriores',
     'Agenda internacional: el presidente participó del Foro de Davos',
     'Milei se reunió con CEOs de Apple, Tesla/SpaceX, Meta y OpenAI, en el marco de la '
     'estrategia oficial de reinserción internacional del país.'),
    ('desarrollo_militar', date(2024, 1, 15), 'Defensa',
     'Lanzamiento del patrullero oceánico "Contralmirante Cordero"',
     'Equipado con tecnología de punta y tripulado por 40 agentes, controla los espacios '
     'marítimos para evitar que buques extranjeros extraigan recursos naturales, según el '
     'Ministerio de Defensa.'),
    ('bienestar', date(2024, 2, 15), 'Salud',
     'DNU 70/23: desregulación de obras sociales y prepagas',
     'El Gobierno definió una nueva reglamentación del marco regulatorio de la medicina '
     'privada y las obras sociales, con el objetivo declarado de dar libertad de elección a '
     'los usuarios e impulsar la competencia.'),
    ('educacion', date(2024, 2, 15), 'Capital Humano',
     'Comenzó la revisión de cinco universidades creadas en 2023',
     'Se auditaron las universidades Madres de Plaza de Mayo, de Ezeiza, Del Delta, de Río '
     'Tercero y de Pilar, para determinar el cumplimiento del procedimiento de creación y su '
     'funcionamiento.'),
    ('institucional', date(2024, 3, 15), 'Justicia',
     'Argentina se incorporó al GAFI para combatir el lavado de activos',
     'El país se sumó al Grupo de Acción Financiera Internacional, creado por el G7, en '
     'materia de prevención y combate del lavado de dinero.'),
    ('institucional', date(2024, 4, 15), 'Justicia',
     'Se lanzó el Programa Nacional de Inteligencia Artificial en la Justicia',
     'Una iniciativa oficial para modernizar procesos judiciales y procedimientos '
     'administrativos mediante la incorporación de nuevas tecnologías.'),
    ('geo', date(2024, 6, 15), 'Relaciones Exteriores',
     'Argentina participó de la cumbre del G7 en Italia',
     'El presidente mantuvo reuniones bilaterales con Giorgia Meloni, Emmanuel Macron, la '
     'titular del FMI Kristalina Georgieva y el presidente del Banco Mundial, Ajay Banga.'),
    ('bienestar', date(2024, 6, 15), 'Capital Humano',
     'El Gobierno anunció que las jubilaciones le ganaron a la inflación en el 1er semestre',
     'Según cifras oficiales, mientras en la gestión anterior las jubilaciones habían caído '
     '24% en términos reales, en el primer semestre de 2024 los jubilados que aportaron '
     'efectivamente le ganaron 4% a la inflación.'),
    ('institucional', date(2024, 7, 15), 'Cambios Base',
     'El Congreso aprobó la Ley Bases',
     'El paquete de reformas incluyó facultades delegadas, privatizaciones, eliminación de '
     'fondos fiduciarios, reforma del empleo público y modernización laboral, entre otros '
     'puntos.'),
    ('institucional', date(2024, 7, 15), 'Cambios Base',
     'Se firmó el Pacto de Mayo con 18 de las 24 provincias',
     'El documento estableció diez puntos centrales de política económica y fiscal como '
     'base de acuerdo entre el Gobierno nacional y los gobernadores firmantes.'),
    ('macro', date(2024, 7, 15), 'Economía',
     'El Gobierno anunció "superávits gemelos" en el primer semestre',
     'Según cifras oficiales, en seis meses se alcanzó un superávit fiscal de $2.572.327 '
     'millones y un superávit comercial de US$10.708 millones.'),
    ('sector_externo', date(2024, 8, 15), 'Economía',
     'Primeras inversiones anunciadas tras la aprobación del RIGI',
     'YPF anunció una inversión de USD 30.000 millones en una planta de GNL en Río Negro y '
     'BHP un proyecto minero en San Juan, entre otros anuncios post-RIGI.'),
    ('institucional', date(2024, 10, 15), 'Cambios Base',
     'Se disolvió la AFIP y fue reemplazada por ARCA',
     'La nueva Agencia de Recaudación y Control Aduanero tiene, según el Gobierno, una '
     'estructura simplificada con una reducción del 34% de los cargos públicos del '
     'organismo.'),
    ('sector_externo', date(2024, 10, 15), 'Economía',
     'Préstamo del Banco Mundial y el BID por USD 8.800 millones',
     'El Gobierno presentó el financiamiento como una señal de confianza internacional en '
     'el rumbo económico, y acordó con el BID una agenda de trabajo conjunta.'),
    ('educacion', date(2024, 12, 15), 'Capital Humano',
     'Transparencia en las Universidades Nacionales',
     'Las universidades públicas quedaron formalmente incluidas en las normativas que '
     'regulan la administración financiera y las contrataciones electrónicas del Estado, a '
     'través de cuatro decretos.'),
    ('seguridad', date(2024, 12, 15), 'Seguridad',
     'Presentación del Plan Güemes contra el narcotráfico en la frontera norte',
     'La ministra de Seguridad, Patricia Bullrich, presentó en Salta un programa para '
     'combatir narcotráfico, sicariato, contrabando y trata de personas en las fronteras, '
     'con mayor presencia policial y controles aduaneros.'),
    ('seguridad', date(2024, 12, 15), 'Seguridad',
     'Plan 90/10 para bajar los homicidios en las grandes ciudades',
     'El plan apunta a reducir los homicidios en las zonas de mayor densidad poblacional, ya '
     'que —según el Gobierno— el 90% se concentra en el 10% del territorio; se aplica en '
     'CABA, PBA, Córdoba, Mendoza, Santa Fe y Tucumán.'),
    ('macro', date(2024, 12, 15), 'Economía',
     'Eliminación del Impuesto País',
     'Las operaciones con dólar tarjeta o ahorro dejaron de pagar el impuesto creado en '
     '2019: el dólar tarjeta pasó de $1.668 a $1.371 para compras y viajes al exterior.'),
    ('seguridad', date(2025, 1, 15), 'Seguridad',
     'Desalojo de tierras usurpadas en el Parque Nacional Los Alerces, Chubut',
     'Se desalojó a un grupo que en 2020 había ocupado áreas del parque; el operativo, a '
     'cargo de la Policía Federal, fue el primero de este tipo en 18 años, según el '
     'Gobierno.'),
    ('bienestar', date(2025, 1, 15), 'Salud',
     'Fin a la intermediación de las prepagas en aportes de la seguridad social',
     'El Ministerio de Salud resolvió que los aportes de los afiliados los reciba '
     'directamente la prepaga u obra social que provee el servicio, sin intermediarios.'),
    ('seguridad', date(2025, 3, 15), 'Seguridad',
     'Presentación de la Ley Antibarras',
     'La iniciativa oficial busca declarar a las "barras bravas" organizaciones criminales, '
     'para que respondan penalmente tanto por hechos dentro como fuera de los estadios.'),
    ('institucional', date(2025, 3, 15), 'Economía',
     'Comenzó el proceso de privatización de Intercargo',
     'Se firmó el decreto que inicia la privatización total de la empresa de servicios '
     'aeroportuarios, incluida en la Ley Bases como sujeta a privatización.'),
    ('macro', date(2025, 4, 15), 'Economía',
     'El Gobierno anunció la salida del cepo cambiario',
     'El BCRA puso en marcha la Fase 3 del programa económico: el dólar pasó a flotar entre '
     'bandas de $1.000 y $1.400, con un paquete de financiamiento de US$32.000 millones del '
     'FMI, el Banco Mundial y el BID.'),
    ('geo', date(2025, 5, 15), 'Relaciones Exteriores',
     'Argentina inició el proceso formal de adhesión a la OCDE',
     'El Secretario General de la OCDE, Mathias Cormann, entregó en París la "Hoja de Ruta" '
     'que marca el comienzo formal del proceso de adhesión del país.'),
    ('pobreza', date(2025, 5, 15), 'Capital Humano',
     'El Gobierno anunció la eliminación de intermediarios en los planes sociales',
     'De 44.000 comedores registrados, según el Gobierno solo se asistía al 10%; se '
     'iniciaron investigaciones a dirigentes sociales por presuntas irregularidades y '
     'malversación de fondos.'),
    ('educacion', date(2025, 7, 15), 'Capital Humano',
     'Lanzamiento de la renovación curricular educativa',
     'La reforma oficial se organiza en torno a cinco ejes: matemática, alfabetización '
     'financiera, habilidades socioemocionales, convivencia escolar e integración de '
     'inteligencia artificial en las aulas.'),
    ('institucional', date(2025, 12, 15), 'Economía',
     'El Congreso aprobó el Presupuesto 2026 con déficit cero',
     'Tras dos años de prórroga del presupuesto heredado, el Gobierno logró la sanción de un '
     'presupuesto con meta de déficit cero — según el propio Ejecutivo, la primera vez en '
     'mucho tiempo.'),
    ('geo', date(2026, 2, 15), 'Relaciones Exteriores',
     'Se aprobó el Acuerdo Mercosur–Unión Europea',
     'El acuerdo, alcanzado políticamente en 2019 tras dos décadas de negociación, habilita '
     'a los productores argentinos a exportar a un mercado de 450 millones de personas.'),
    ('empleo', date(2026, 2, 15), 'Economía',
     'Se sancionó la Ley de Modernización Laboral',
     'El Gobierno la calificó como el mayor cambio al esquema laboral en cinco décadas; '
     'prevé la posibilidad de regularizar a la mitad de los trabajadores que hoy están en la '
     'informalidad.'),
    ('seguridad', date(2026, 2, 15), 'Justicia',
     'Se sancionó la Ley Penal Juvenil',
     'La norma bajó la edad de imputabilidad a los 14 años; el Gobierno sostuvo que le da a '
     'la Justicia más instrumentos para intervenir con menores en conflicto con la ley.'),
    ('pobreza', date(2026, 3, 15), 'Economía',
     'INDEC: la pobreza bajó al nivel más bajo en 7 años',
     'Según la medición oficial del segundo semestre de 2025, la pobreza se ubicó en 28,2%, '
     '9,9 puntos porcentuales menos que el semestre anterior.'),
    ('sector_externo', date(2026, 3, 15), 'Relaciones Exteriores',
     'Se anunciaron US$16.150 millones en inversiones tras el "Argentina Week"',
     'Entre los anuncios figuraron US$3.400 millones de Mercado Libre, US$3.000 millones de '
     'TGS en Vaca Muerta y US$4.500 millones de Pampa Energía en petróleo no convencional.'),
    ('institucional', date(2026, 4, 15), 'Interior',
     'Se envió al Congreso el proyecto de Reforma Electoral',
     'La iniciativa oficial plantea eliminar las PASO, terminar con los partidos "sello de '
     'goma" que reciben financiamiento estatal sin representar votantes, y transparentar el '
     'financiamiento partidario.'),
    ('desarrollo_militar', date(2026, 4, 15), 'Defensa',
     'Puesta en marcha del Plan ARMA de reequipamiento militar',
     'Establece que el 10% de lo recaudado por venta o alquiler de bienes del Estado se '
     'destine al reequipamiento y modernización de las Fuerzas Armadas.'),
    ('institucional', date(2026, 6, 15), 'Economía',
     'Se completó la privatización de la Vía Navegable Troncal',
     'Se adjudicó la concesión de la hidrovía a la firma Jan de Nul–Servimagnus, con una '
     'baja proyectada del 13,5% en los costos logísticos para los productores, según el '
     'Gobierno.'),
    ('produccion', date(2026, 7, 15), 'Economía',
     'La campaña de soja alcanzó la segunda mejor producción en 5 años',
     'Según cifras oficiales, la cosecha llegó a 49.700.000 toneladas, con rendimientos que '
     'superaron los 3.000 kilos por hectárea sobre 16,3 millones de hectáreas sembradas.'),
    ('geo', date(2026, 8, 15), 'Economía',
     'El BCRA renovó el swap de monedas con China por cinco años',
     'El acuerdo con el Banco Popular de China extendió el plazo de tres a cinco años; la '
     'activación de 35.000 millones de renminbi (unos US$5.000 millones) sigue vigente.'),
]


class Command(BaseCommand):
    help = (
        'Carga una selección curada de la Bitácora de gestión oficial (argentina.gob.ar) '
        'como Noticias y eventos de línea de tiempo, con medio_id=presidencia-nacion.'
    )

    def handle(self, *args, **options):
        noticias_cargadas = 0
        eventos_cargados = 0

        for cat_id, fecha, kicker, titulo, bajada in ENTRADAS:
            Noticia.objects.update_or_create(
                titulo=titulo,
                defaults={
                    'categoria_id': cat_id, 'medio_id': MEDIO_ID, 'fecha': fecha,
                    'kicker': kicker, 'bajada': bajada, 'url': URL_BITACORA,
                    'publicado': True,
                },
            )
            noticias_cargadas += 1

            EventoTimeline.objects.update_or_create(
                titulo=titulo, fecha=fecha,
                defaults={'categoria_id': cat_id, 'sentimiento': 'neutral', 'fuente_id': None},
            )
            eventos_cargados += 1

        self.stdout.write(self.style.SUCCESS(
            f'{noticias_cargadas} noticias y {eventos_cargados} eventos de la bitácora oficial OK.'
        ))
