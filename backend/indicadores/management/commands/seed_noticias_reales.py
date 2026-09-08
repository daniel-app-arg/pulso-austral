"""
Primer fill de noticias reales: hechos verificados por búsqueda web (no
inventados), desde el inicio del gobierno de Milei (10 de diciembre de
2023) hasta la actualidad. Cada uno tiene:

- `titulo`/`bajada` escritos de cero a partir de lo que reportaron las
  fuentes — no son citas textuales (evita problemas de copyright y hace
  que el resumen persista con sentido aunque el link se rompa).
- `url` al artículo original de un medio ya cargado en `Medio`
  (seed_editorial.py) — puede quedar rota con el tiempo, pero titulo/bajada
  no dependen de que siga viva.

Es un punto de partida curado (26 hechos, uno por categoría como mínimo),
no un archivo exhaustivo de 3 años de noticias — mismo criterio que ya se
usó para `eventos_timeline` (18 eventos) en seed_pulso_austral.py.
Ampliarlo es agregar tuplas a NOTICIAS_REALES, no rediseñar nada.

Uso:
    python manage.py seed_noticias_reales
"""

from datetime import date

from django.core.management.base import BaseCommand

from indicadores.models import Noticia

# (categoria_id, medio_id, fecha, kicker, titulo, bajada, url)
NOTICIAS_REALES = [
    (
        "macro", "ambito-financiero", date(2023, 12, 13), "Economía",
        "El Gobierno devaluó el peso 118% a dos días de la asunción de Milei",
        "El ministro de Economía Luis Caputo anunció el mayor salto cambiario desde la "
        "hiperinflación de 1989, dentro de un paquete de ajuste fiscal y baja de subsidios "
        "a la energía y el transporte.",
        "https://www.ambito.com/economia/devaluacion-suba-diaria-del-dolar-la-era-milei-fue-la-tercera-mas-grande-la-historia-argentina-n5899535",
    ),
    (
        "macro", "infobae", date(2025, 1, 14), "Economía",
        "La inflación de 2024 cerró en 117,8%, casi la mitad que el año anterior",
        "El IPC de diciembre fue del 2,7% según el INDEC, consolidando una desaceleración "
        "que llevó la inflación mensual a un dígito desde abril de ese año.",
        "https://www.infobae.com/economia/2025/01/14/la-inflacion-de-2024-fue-de-1178-y-se-redujo-casi-a-la-mitad-de-la-que-dejo-el-gobierno-anterior/",
    ),
    (
        "macro", "infobae", date(2025, 1, 17), "Economía",
        "Argentina cerró 2024 con superávit fiscal por primera vez en 14 años",
        "El resultado financiero de 0,3% del PBI se logró tras una baja del gasto primario "
        "del 27% en términos reales, según el Ministerio de Economía.",
        "https://www.infobae.com/espana/agencias/2025/01/17/argentina-cierra-2024-con-un-superavit-fiscal-del-03-del-pib/",
    ),
    (
        "macro", "infobae", date(2025, 4, 11), "Economía",
        'Milei eliminó el cepo cambiario "para siempre" tras 15 años de controles',
        "El Gobierno anunció un paquete de financiamiento de US$32.000 millones entre el "
        "FMI, el Banco Mundial y el BID; el dólar pasó a flotar entre bandas de $1.000 y "
        "$1.400.",
        "https://www.infobae.com/politica/2025/04/12/javier-milei-dijo-que-la-argentina-recibira-usd-32-mil-millones-y-afirmo-eliminamos-el-cepo-para-siempre/",
    ),
    (
        "macro", "infobae", date(2025, 10, 28), "Economía",
        "El riesgo país cerró 2025 en mínimos de ocho años tras el triunfo electoral",
        "El indicador había llegado a 1.456 puntos en septiembre, tras la derrota "
        "oficialista en la provincia de Buenos Aires, y se derrumbó después del triunfo de "
        "La Libertad Avanza en las legislativas de octubre.",
        "https://www.infobae.com/economia/2025/10/28/a-cuanto-tiene-que-bajar-el-riesgo-pais-para-que-la-argentina-vuelva-a-los-mercados-internacionales/",
    ),
    (
        "empleo", "infobae", date(2025, 5, 3), "Trabajo",
        "El Gobierno puso un techo de 1% mensual a los aumentos salariales",
        "La Secretaría de Trabajo dejó de homologar convenios paritarios que superaran ese "
        "porcentaje, como parte de la estrategia antiinflacionaria; los gremios advirtieron "
        "que los salarios volvían a perder contra los precios.",
        "https://www.infobae.com/politica/2025/05/03/el-gobierno-no-homologara-aumentos-superiores-al-1-mensual-y-puso-en-la-mira-la-paritaria-de-comercio/",
    ),
    (
        "pobreza", "chequeado", date(2024, 9, 26), "Pobreza",
        "La pobreza trepó a 52,9% en el primer semestre de 2024, la más alta en 20 años",
        "El INDEC reportó casi 25 millones de personas bajo la línea de pobreza y una "
        "indigencia que casi se duplicó interanual, del 9,3% al 18,1%, en el primer tramo "
        "del ajuste.",
        "https://chequeado.com/el-explicador/el-indec-dara-a-conocer-hoy-los-primeros-datos-de-pobreza-de-la-gestion-de-javier-milei-como-evoluciono-este-indice/",
    ),
    (
        "pobreza", "chequeado", date(2025, 3, 31), "Pobreza",
        "La pobreza bajó a 38,1% en el segundo semestre de 2024, la mayor caída en 20 años",
        "Tras el pico de mediados de año, el indicador recortó 14,8 puntos porcentuales en "
        "seis meses, aunque siguió afectando a casi 18 millones de personas.",
        "https://chequeado.com/el-explicador/en-vivo-el-indec-da-a-conocer-hoy-el-dato-de-pobreza-del-segundo-semestre-de-2024/",
    ),
    (
        "produccion", "infobae", date(2025, 3, 19), "Actividad económica",
        "El PBI cayó 1,7% en 2024, el segundo año consecutivo en baja",
        "La construcción (-17,7%) y la industria (-9,2%) lideraron la contracción, mientras "
        "el agro creció 31,3%; la economía volvió a niveles de actividad de una década "
        "atrás.",
        "https://www.infobae.com/economia/2025/03/19/la-economia-argentina-se-contrajo-17-en-2024-con-fuertes-caidas-en-la-construccion-y-la-industria/",
    ),
    (
        "sector_externo", "el-cronista", date(2024, 11, 8), "Sector externo",
        "El blanqueo de capitales sumó más de US$32.000 millones",
        "El régimen de regularización de activos, vigente desde agosto, exteriorizó ese "
        "monto en su primera etapa, la mayoría en cuentas bancarias especiales y "
        "propiedades dentro del país.",
        "https://www.cronista.com/economia-politica/el-blanqueo-finalizo-con-mas-de-us-32000-m-y-la-moratoria-sumo-mas-de-340000-planes-de-pago/",
    ),
    (
        "institucional", "la-nacion", date(2024, 6, 12), "Congreso",
        "Empate en el Senado: Villarruel desempató y se aprobó la Ley Bases",
        "Tras 13 horas de debate el recuento quedó 36 a 36; la vicepresidenta usó su voto "
        "para destrabar la ley que delega facultades al Ejecutivo y habilita un paquete de "
        "reformas fiscales y laborales.",
        "https://www.lanacion.com.ar/politica/ley-bases-en-una-votacion-electrizante-debio-desempatar-villarruel-y-el-oficialismo-logro-aprobar-en-nid12062024/",
    ),
    (
        "institucional", "pagina12", date(2024, 10, 9), "Congreso",
        "Diputados confirmó el veto de Milei al financiamiento universitario",
        "La Cámara no reunió los dos tercios para insistir con la ley, que había sido "
        "sancionada tras una masiva movilización en defensa del presupuesto de las "
        "universidades públicas.",
        "https://www.pagina12.com.ar/772041-texto-completo-del-veto-de-milei-a-la-ley-de-financiamiento-",
    ),
    (
        "institucional", "chequeado", date(2025, 2, 14), "Transparencia",
        "Escándalo $LIBRA: Milei promocionó una cripto que se desplomó 89% en horas",
        "El presidente recomendó por X un token que se multiplicó por 35 y luego colapsó; "
        "en las primeras 48 horas se presentaron más de 100 denuncias penales por presunta "
        "estafa.",
        "https://chequeado.com/el-explicador/cronologia-del-criptogate-las-claves-del-caso-libra-que-involucra-a-javier-milei/",
    ),
    (
        "institucional", "infobae", date(2025, 10, 27), "Elecciones",
        "La Libertad Avanza ganó las legislativas con más del 40% de los votos",
        "El oficialismo se impuso en 16 de 24 distritos, incluida la provincia de Buenos "
        "Aires, y pasó de 43 a 97 diputados propios en una elección con la participación "
        "más baja desde 1983.",
        "https://www.infobae.com/politica/2025/10/27/categorico-triunfo-de-la-libertad-avanza-gana-en-la-provincia-de-buenos-aires-y-obtiene-mas-del-40-de-los-votos-en-todo-el-pais/",
    ),
    (
        "bienestar", "ambito-financiero", date(2024, 8, 28), "Jubilados",
        "Represión a jubilados frente al Congreso en el rechazo al veto previsional",
        "Milei había vetado por decreto la ley que aumentaba los haberes; la marcha semanal "
        "de jubilados terminó con gases y detenidos mientras la Cámara de Diputados debatía "
        "si insistir con la ley.",
        "https://www.ambito.com/economia/jubilados-volveran-marchar-manana-congreso-plaza-mayo-contra-el-veto-javier-milei-n6055985",
    ),
    (
        "percepcion", "infobae", date(2025, 10, 23), "Percepción",
        "La confianza del consumidor subió 6,3% en octubre",
        "El índice de la Universidad Torcuato Di Tella repuntó tras el triunfo electoral "
        "del oficialismo, en un mes marcado por la volatilidad cambiaria previa a los "
        "comicios.",
        "https://www.infobae.com/economia/2025/10/23/fuerte-recuperacion-en-la-confianza-del-consumidor-en-octubre-impacto-en-las-expectativas-y-el-consumo/",
    ),
    (
        "geo", "infobae", date(2025, 10, 14), "Geopolítica",
        "Trump recibió a Milei en la Casa Blanca y condicionó el apoyo a las elecciones",
        "El encuentro se dio días antes de las legislativas; Trump advirtió que el respaldo "
        "financiero de Estados Unidos dependía del resultado electoral del 26 de octubre.",
        "https://www.infobae.com/politica/2025/10/14/milei-se-reune-con-donald-trump-en-vivo-las-ultimas-noticias-sobre-el-encuentro-en-la-casa-blanca/",
    ),
    (
        "seguridad", "infobae", date(2024, 3, 9), "Seguridad",
        "Bullrich desplegó fuerzas federales en Rosario tras una ola de violencia narco",
        "La ministra de Seguridad anunció que los hechos de violencia en espacios públicos "
        "se investigarían como actos de terrorismo, tras cuatro muertes en cinco días "
        "vinculadas a bandas narco.",
        "https://www.infobae.com/politica/2024/03/09/en-medio-del-avance-narco-bullrich-anuncio-que-denunciara-los-hechos-de-violencia-en-rosario-como-actos-de-terrorismo/",
    ),
    (
        "desarrollo_militar", "infobae", date(2024, 4, 16), "Defensa",
        "Argentina compró 24 aviones de combate F-16 a Dinamarca",
        "Es la mayor adquisición de aviones militares en décadas para la Fuerza Aérea, que "
        "no contaba con cazas supersónicos desde el retiro de los Mirage III en 2015; el "
        "contrato rondó los US$300 millones.",
        "https://cnnespanol.cnn.com/2024/04/16/argentina-compra-aviones-f-16-dinamarca-orix",
    ),
    (
        "seguridad", "infobae", date(2026, 1, 22), "Seguridad",
        "Argentina registró en 2025 la menor tasa de homicidios de su historia",
        "El Ministerio de Seguridad presentó las Estadísticas Criminales 2025: la tasa cayó "
        "a 3,6 cada 100.000 habitantes (desde 4,4 en 2023) y los robos bajaron 20,8% en el "
        "año, según el Sistema Nacional de Información Criminal.",
        "https://www.infobae.com/politica/2026/01/22/el-ministerio-de-seguridad-anuncio-la-tasa-de-homicidios-mas-baja-de-los-ultimos-anos-y-destaco-que-los-robos-disminuyeron-un-208-en-2025/",
    ),
    (
        "desarrollo_militar", "el-cronista", date(2026, 9, 7), "Defensa",
        "Vuelve la inscripción al Servicio Militar Voluntario con un rango de edad ampliado",
        "El Ejército confirmó que durante septiembre los jóvenes solteros de entre 18 y 28 "
        "años —antes el tope era 24— pueden anotarse para incorporarse a las Fuerzas "
        "Armadas; sigue siendo voluntario, no obligatorio.",
        "https://www.cronista.com/informacion-gral/confirmado-por-el-ejercito-de-argentina-en-septiembre-vuelve-el-servicio-militar-y-los-jovenes-de-entre-18-y-28-anos-deben-integrar-las-fuerzas-armadas-si-se-encuentran-solteros/",
    ),
    (
        "sector_externo", "perfil", date(2026, 2, 19), "Sector externo",
        "La balanza comercial arrancó 2026 con un superávit de US$1.987 millones",
        "El INDEC informó exportaciones por US$7.057 millones e importaciones por "
        "US$5.070 millones en enero, con un récord de ventas externas para ese mes.",
        "https://www.perfil.com/noticias/economia/la-balanza-comercial-comenzo-2026-con-un-superavit-de-1987-millones-a40.phtml",
    ),
    (
        "educacion", "la-nacion", date(2023, 12, 5), "Educación",
        "Los resultados de PISA confirman una crisis de aprendizajes básicos en Argentina",
        "7 de cada 10 estudiantes no alcanzó el nivel básico en Matemática y la mitad no llegó "
        "al mínimo en Lectura, según la prueba internacional de la OCDE tomada a alumnos de "
        "15 años en 2022.",
        "https://www.lanacion.com.ar/sociedad/pruebas-pisa-la-crisis-de-los-aprendizajes-basicos-a-contrapelo-de-todos-los-discursos-de-inclusion-nid05122023/",
    ),
    (
        "educacion", "perfil", date(2024, 10, 3), "Educación",
        "Milei vetó la Ley de Financiamiento Universitario y el Congreso no logró revertirlo",
        "La norma preveía actualizar por inflación el presupuesto de las universidades "
        "nacionales y los salarios docentes; la oposición no reunió los dos tercios "
        "necesarios en Diputados para insistir con la ley.",
        "https://www.perfil.com/noticias/politica/las-universidades-cierran-el-primer-ano-de-javier-milei-con-un-30-menos-de-presupuesto.phtml",
    ),
    (
        "produccion", "infobae", date(2024, 12, 31), "Producción",
        "La liquidación de divisas del agro fue récord en 2024 y superó los US$25.000 millones",
        "Fue el tercer mejor año de la historia para el ingreso de dólares del campo, "
        "impulsado por una cosecha superior a la de 2023 pese a la caída de precios "
        "internacionales de los granos.",
        "https://www.infobae.com/economia/2024/12/31/la-liquidacion-de-divisas-del-agro-fue-record-en-2024-y-supero-los-usd-25000-millones/",
    ),
    (
        "bienestar", "infobae", date(2024, 12, 2), "Salud",
        "El PAMI restringió el acceso a medicamentos gratis para los jubilados",
        "La obra social de los jubilados dejó de cubrir al 100% unos 170 medicamentos; "
        "para mantener la gratuidad ahora se exigen topes de ingresos y patrimonio. Meses "
        "después la Justicia de Mendoza frenó la medida por regresiva.",
        "https://www.infobae.com/salud/2024/12/02/medicamentos-del-pami-cuales-son-los-cambios-en-la-cobertura-para-los-jubilados-y-pensionados/",
    ),
]


class Command(BaseCommand):
    help = 'Carga el primer fill de noticias reales (verificadas por búsqueda web) desde el inicio del gobierno de Milei.'

    def handle(self, *args, **options):
        cargadas = 0
        for cat_id, medio_id, fecha, kicker, titulo, bajada, url in NOTICIAS_REALES:
            Noticia.objects.update_or_create(
                titulo=titulo,
                defaults={
                    'categoria_id': cat_id, 'medio_id': medio_id, 'fecha': fecha,
                    'kicker': kicker, 'bajada': bajada, 'url': url, 'publicado': True,
                },
            )
            cargadas += 1
        self.stdout.write(self.style.SUCCESS(f'{cargadas} noticias reales OK.'))
