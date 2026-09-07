# Pulso Austral — backend (Django)

Reemplaza a Supabase como fuente de datos. API de solo lectura para el
frontend (React/Next.js); la escritura se hace desde el Django admin o desde
comandos de management — nunca desde un endpoint público (mismo principio
que la RLS del `pulso-austral-schema.sql` original).

## Arrancar en local

```bash
cd backend
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py seed_pulso_austral   # datos de ejemplo
./venv/Scripts/python.exe manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/ (usuario `admin`, password `pulsoaustral2026` —
**cambiarla**, se creó solo para este entorno de desarrollo local).

Copiar `.env.example` a `.env` para configurar `SECRET_KEY`, `DATABASE_URL`
(Postgres en producción; SQLite por defecto) y `CORS_ALLOWED_ORIGINS`.

## Base de datos en Neon (Postgres)

[Neon](https://neon.tech) es Postgres serverless con un plan gratuito
generoso — recomendado para este proyecto en vez de mantener SQLite.
Crear la cuenta y el proyecto es algo que tenés que hacer vos (no puedo
crear cuentas en servicios externos); el resto lo dejo armado para que sea
copiar y pegar un string.

**1. Crear el proyecto** (una sola vez)
1. Entrar a https://console.neon.tech/ y crear una cuenta (GitHub, Google o email).
2. "Create a project" → nombre `pulso-austral` → elegir la región más
   cercana disponible (si aparece alguna en Sudamérica, esa; si no, la más
   próxima).
3. En el dashboard del proyecto, pestaña **Connect** / **Connection Details**:
   copiar el **connection string** completo (empieza con `postgresql://...`
   y ya trae `?sslmode=require`). Elegir la variante **pooled** si Neon la
   ofrece separada — está pensada justo para apps con muchas conexiones
   cortas como esta.

**2. Conectar el backend**

Pegar ese string en `backend/.env` (no en el chat — es información
sensible, y esto queda en tu máquina):
```
DATABASE_URL=postgresql://usuario:password@ep-xxx-pooler.region.aws.neon.tech/pulso_austral?sslmode=require
```

**3. Migrar y recargar los datos**

Los datos actuales en SQLite son 100% reproducibles (seeds + fetch a
fuentes reales), así que no hace falta migrar filas a mano — alcanza con
recrear el esquema y volver a correr los mismos comandos contra Neon:
```bash
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py seed_pulso_austral
./venv/Scripts/python.exe manage.py seed_editorial
./venv/Scripts/python.exe manage.py fetch_datos_reales
./venv/Scripts/python.exe manage.py createsuperuser
```

`seed_pulso_austral` y `fetch_datos_reales` escriben los ~1.800 puntos de
`IndicadorValor` con un `bulk_create(update_conflicts=True)` (upsert en
lote vía `ON CONFLICT DO UPDATE`) en vez de un `update_or_create` por fila
— contra Neon tardan ~1 minuto y ~10 segundos respectivamente (antes,
fila por fila, 10-20 minutos). Si se agrega un nuevo comando que escriba
muchas filas, conviene seguir el mismo patrón: acumular objetos en una
lista y un solo `bulk_create` al final, no un `update_or_create` por
punto — cada uno de esos es 2 viajes de red contra una base remota.

**4. Verificar**
```bash
./venv/Scripts/python.exe manage.py dbshell   # debería abrir psql contra Neon, no sqlite3
```
o simplemente levantar `runserver` y pegarle a `/api/categorias/` — si
responde, ya está leyendo de Neon.

Los settings (`config/settings.py`) leen `DATABASE_URL` con
`dj_database_url.parse()` vía `python-decouple`, y fuerzan `sslmode=require`
si por algún motivo la URL no lo trae — no hace falta tocar código.

## Qué se actualiza solo y qué no

`Indicador.actualizacion_automatica` (bool) distingue, en la base y en la
API (`/api/indicadores/?actualizacion_automatica=true`), los indicadores
con datos reales de una fuente externa (los 6 que toca
`fetch_datos_reales`: dólar oficial/blue, reservas BCRA, inflación
interanual, EMAE, desempleo) del resto — ilustrativos o editoriales, que no
necesitan actualizarse nunca. El flag lo fijan **dos** comandos a
propósito, en vez de uno: `seed_pulso_austral.py` (vía el set
`INDICADORES_CON_DATOS_REALES`) y `fetch_datos_reales.py` (vía
`Command.INDICADORES_GESTIONADOS`, al final de `handle()`) — así, si en el
futuro se agrega un indicador nuevo a `fetch_datos_reales.py` y alguien se
olvida de sumarlo también a la lista del seed, el propio comando de
ingesta lo termina marcando bien de todos modos.

## Índice general ("¿el país mejora o empeora?")

Ver `indicadores/services/pulso_index.py` para la metodología completa
(está documentada ahí, no solo acá). Resumen:

- Solo entran los indicadores numéricos con `Indicador.polaridad` definida
  ('positivo' = subir es mejorar, 'negativo' = subir es empeorar) — todo
  lo ideológicamente contestado (dólar, Merval, desarrollo militar,
  aprobación/confianza en el gobierno, gasto público, canasta básica
  nominal) queda en 'neutral' **a propósito**, y por lo tanto afuera. Las
  polaridades se fijan en `seed_pulso_austral.py` (dict `POLARIDADES`,
  con el razonamiento de cada exclusión comentado ahí mismo).
- Para cada uno se mira el `trend` de su último valor cargado (el mismo
  que ya se ve en su tarjeta) y se cuenta cuántos mejoran/empeoran/quedan
  igual. Score = índice de difusión 0-100 (50 + 50×(mejoran−empeoran)/total),
  no un promedio de unidades distintas.
- `python manage.py compute_pulso_index` calcula el score de hoy y guarda
  una foto en `PulsoIndexSnapshot` (una fila por día que se corre) — así
  `/api/pulso-index/` puede mostrar la tendencia del índice mismo (¿subió
  o bajó desde la foto anterior?), no solo un número suelto. Sin fotos
  guardadas, el endpoint cae a calcular en vivo (sin tendencia propia).
  Mismo criterio que `fetch_datos_reales`: no hay scheduler corriendo esto
  todavía, es manual hasta que se decida el despliegue.

**Bug real encontrado y corregido en el camino**: al optimizar la consulta
(una sola query para el último valor de todos los indicadores en vez de
una por indicador — mismo patrón de la sección de arriba), un indicador
con dos puntos en la misma fecha pero distinta granularidad (pasa seguido:
el resample anual/mensual cae el mismo día que el punto más fino cuando
ese es el último dato disponible) podía desempatar hacia cualquiera de los
dos sin garantía — `inflacion_interanual` cambió de "mejora" a "empeora"
entre una versión y otra del código sin que cambiara ningún dato real. Se
resolvió con un desempate explícito por prioridad de granularidad
(mes > año > semana > día, el mismo criterio que ya usa el frontend para
elegir qué delta mostrar en la tarjeta) en vez de confiar en el orden que
devuelva la base.

**Todavía no hay ningún scheduler** corriendo `fetch_datos_reales`
automáticamente — es 100% manual por ahora. Se decidió a propósito no
armar un cron local (Windows Task Scheduler) porque no tiene sentido
mantenerlo una vez que esto se despliegue a un servidor real; ahí sí
conviene un cron job del lado del servidor (Celery beat, cron de
Render/Railway, GitHub Actions programado, etc.) — pendiente hasta que se
decida el despliegue.

## Modelos (`indicadores/models.py`)

Las 6 tablas del SQL original: `Fuente`, `Categoria`, `Indicador`,
`IndicadorValor` (la serie de tiempo), `EventoTimeline`, `Noticia`. Más dos
agregadas para contenido editorial: `Medio` (directorio de medios de
comunicación con una caracterización de orientación política — ver seed
más abajo) y `Gobierno` (períodos presidenciales de 4 años, para resumir
todos los indicadores por mandato).

## API (`/api/`)

Todo de solo lectura (`AllowAny`, sin métodos de escritura expuestos):

- `GET /api/categorias/`
- `GET /api/fuentes/`
- `GET /api/indicadores/?categoria=<id>&destacado=true&tipo=numerico`
- `GET /api/indicador-valores/?indicador=<id>&granularidad=dia|semana|mes|anio`
- `GET /api/eventos-timeline/?categoria=<id>&sentimiento=positivo|negativo|neutral`
- `GET /api/noticias/?categoria=<id>` (solo `publicado=true` salvo que se pida explícito)
- `GET /api/destacados/` — dólar oficial/blue, Merval y brecha ya calculada (header)
- `GET /api/ultimos-valores/` — equivalente a la vista SQL `ultimos_valores`
- `GET /api/timeline-resumen-mensual/` — equivalente a la vista SQL `timeline_resumen_mensual`
- `GET /api/medios/?tipo=diario&orientacion=centro` — directorio de medios
- `GET /api/gobiernos/` — períodos presidenciales
- `GET /api/gobiernos/<id>/resumen/` — todos los indicadores resumidos para
  ese mandato: valor al inicio, al final (o a hoy si sigue en curso),
  variación absoluta y % (el % se omite si el valor inicial es negativo o
  cero, porque dividir por una base negativa invierte el signo de forma
  contraintuitiva) y promedio del período. Usa, por indicador, la
  granularidad con más puntos dentro del rango — así no mezcla, por
  ejemplo, un punto diario con uno mensual del mismo indicador. Si un
  indicador no tiene ningún punto en el rango, devuelve `sin_datos: true`
  en vez de omitirlo (pasa con los mandatos anteriores a la ventana de
  datos reales que tenemos, ~2017 en adelante para series anuales).

## Seed (`indicadores/management/commands/seed_pulso_austral.py`)

Carga las 9 categorías, 13 fuentes y 39 indicadores con series mensuales (14
puntos, ago-25 a sep-26) y anuales (10 puntos, 2017-2026):

- **macro** (7): dólar oficial/blue, Merval (destacados), inflación, riesgo
  país, reservas BCRA, resultado fiscal — ya venían del mock del artifact.
- **empleo** (4): desempleo, salario real, empleo informal, canasta básica —
  también del mock original.
- **pobreza** (4): tasa de pobreza, indigencia, Gini, brecha de ingresos.
- **produccion** (4): EMAE, IPI manufacturero, capacidad instalada,
  producción agropecuaria.
- **sector_externo** (4): balanza comercial, cuenta corriente, deuda
  externa, exportaciones.
- **institucional** (4): percepción de corrupción, estado de derecho, gasto
  público, confianza en el gobierno.
- **bienestar** (4): esperanza de vida, cobertura de salud, mortalidad
  infantil, acceso a servicios básicos.
- **percepcion** (4): confianza del consumidor, expectativas de inflación
  (REM), humor social, aprobación de gestión.
- **geo** (4): cualitativos (acuerdo FMI, calificación soberana, swap con
  China, Mercosur–UE) — sin serie, un solo valor "actual".
- **seguridad** (4): tasa de homicidios, delitos contra la propiedad, tasa
  de encarcelamiento, percepción de inseguridad.
- **desarrollo_militar** (4): gasto en defensa, efectivos de las FFAA,
  inversión en equipamiento, ranking de poder militar (Global Firepower).

Todas las categorías, salvo geo (cualitativa), tienen granularidades `mes` y
`anio`; `dia`/`semana` quedan pendientes de una fuente real (ver abajo). Los
valores de pobreza/producción/sector_externo/institucional/bienestar/percepcion
son **ilustrativos** — coherentes entre sí y con la narrativa macro del mock
original, pero no series oficiales; hay que reemplazarlos cuando se conecte
cada fuente real (INDEC, BCRA, UTDT, Transparencia Internacional, etc.).
`--flush` borra todo antes de recargar; sin esa flag el comando es idempotente
(`update_or_create`).

⚠️ **Orden de comandos**: este seed reescribe TODOS los indicadores,
incluidos los que ya tienen datos reales (dolar_oficial, dolar_blue,
reservas_bcra, inflacion_interanual, emae, desempleo) — si ya corriste
`fetch_datos_reales`, volvé a correrlo después de este seed para
restaurar los valores reales:
```bash
./venv/Scripts/python.exe manage.py seed_pulso_austral
./venv/Scripts/python.exe manage.py fetch_datos_reales
```

## Datos reales (`indicadores/management/commands/fetch_datos_reales.py`)

```bash
./venv/Scripts/python.exe manage.py fetch_datos_reales
```

Reemplaza los valores ilustrativos de 4 indicadores por datos de fuentes
públicas reales, sin API key:

- **`dolar_oficial`** y **`reservas_bcra`**: serie diaria completa (día,
  semana y mes derivados de la misma serie) de la API "Estadísticas
  Monetarias" del BCRA v4.0 (`indicadores/services/bcra.py`; variables 4 y 1
  del catálogo público). Es la primera vez que hay datos reales en
  granularidad `dia` — antes solo existían mes/año ilustrativos.
- **`inflacion_interanual`**: serie mensual real (10 años) de la misma API
  del BCRA (variable 28), con `anio` derivado del último mes cargado de
  cada año.
- **`dolar_blue`**: solo el valor del día — es un mercado informal, el BCRA
  no lo publica — vía dolarapi.com (`indicadores/services/dolarapi.py`).
- **`emae`** y **`desempleo`**: series de INDEC agregadas por la API de
  datos.gob.ar (`indicadores/services/datos_gob_ar.py`). El desempleo es
  trimestral en origen — se guarda igual bajo granularidad `mes` (con la
  fecha de inicio del trimestre), mismo criterio que para otras series de
  baja frecuencia.

El comando es idempotente (`update_or_create`) y limpia los resabios del
seed ilustrativo que quedan más allá del último dato real disponible (el
BCRA publica con 1-3 días hábiles de rezago), así que se puede correr
periódicamente sin curar nada a mano — pensado para un cron/Celery beat.

**Nota TLS**: `curl` contra `api.bcra.gob.ar` falla con "unable to get local
issuer certificate" porque el bundle de certificados de Git Bash está
desactualizado — no es un problema del certificado del BCRA. `requests`
(vía `certifi`) valida la cadena sin problema; el cliente en `bcra.py` nunca
pasa `verify=False`.

**Merval y riesgo país siguen ilustrativos**: no encontramos una fuente
pública gratuita y sin autenticación equivalente a la del BCRA para estos
dos. Conectarlos implica registrarse en una API de mercado (ByMA/IOL/etc.)
o pagar un feed — pendiente de decisión, no de código. Tampoco encontramos
en datos.gob.ar una serie nacional de pobreza/indigencia ni de canasta
básica que estuviera actualizada (las que hay quedaron en 2024/2025 o son
solo de CABA) — siguen ilustrativas.

## Contenido editorial (`indicadores/management/commands/seed_editorial.py`)

```bash
./venv/Scripts/python.exe manage.py seed_editorial
```

Carga dos cosas que no son series de datos sino contenido curado del sitio:

- **14 medios de comunicación** (`Medio`), cada uno con una `descripcion`
  que explica de dónde sale la caracterización de orientación (línea
  editorial histórica, grupo mediático al que pertenece), no solo la
  etiqueta. Es una clasificación de referencia — mismo espíritu que un
  "media bias chart" — pensada para revisarse a mano desde el admin, no
  una medición objetiva.
- **6 gobiernos** (`Gobierno`): los mandatos presidenciales de 4 años desde
  la reforma constitucional de 1994 (Néstor Kirchner en adelante). El de
  Milei queda con `fecha_fin=None` (en curso).
- **Metodología de 47 indicadores** (`Indicador.metodologia`): qué mide y
  de dónde sale cada uno, para la sección `/glosario` del frontend — dict
  `METODOLOGIAS` en el mismo archivo.

## Noticias reales (`indicadores/management/commands/seed_noticias_reales.py`)

```bash
./venv/Scripts/python.exe manage.py seed_noticias_reales
```

Primer fill de noticias — **19 hechos reales, verificados por búsqueda
web** (no inventados), desde el inicio del gobierno de Milei (10 de
diciembre de 2023) hasta la actualidad, con al menos una por cada una de
las 11 categorías. Cada noticia tiene:

- `titulo`/`bajada` escritos de cero a partir de lo reportado por las
  fuentes (no citas textuales) — es la parte que **persiste** aunque el
  link se rompa.
- `url` al artículo original — probado uno por uno con `curl`, los 19
  responden 200 al momento de cargarlos. Puede quedar rota con el tiempo;
  eso no borra la noticia ni su resumen.
- `medio` (FK a `Medio`, no a `Fuente` — una noticia la escribe un medio de
  comunicación, no un organismo estadístico) cuando el artículo es de uno
  de los 14 medios ya cargados; puede quedar `null` si la fuente real no
  está en esa lista.

Es un punto de partida curado, no un archivo exhaustivo de 3 años de
noticias — mismo criterio que ya se usó para `eventos_timeline` (18
eventos). Ampliarlo es agregar tuplas a `NOTICIAS_REALES`, no rediseñar
nada.

## Pendiente

- [ ] Conectar Merval y riesgo país a una fuente real (requiere elegir/pagar una API de mercado)
- [ ] Reemplazar los valores ilustrativos de pobreza, producción (salvo EMAE), sector_externo, institucional, bienestar y percepcion — la mayoría no tiene una fuente pública tan simple como la del BCRA/datos.gob.ar
- [ ] Cron / Celery beat que corra `fetch_datos_reales` periódicamente
- [ ] Revisar a mano las caracterizaciones de `seed_editorial` (es un punto de partida, no la última palabra)
- [ ] Cargar series reales anteriores a 2017 para que la comparativa por gobierno tenga datos de los mandatos de Kirchner/CFK/Macri (hoy aparecen total o parcialmente `sin_datos`)
- [ ] Ampliar `seed_noticias_reales` más allá de las 19 noticias iniciales (agregar tuplas a `NOTICIAS_REALES`)
- [ ] Completar metodologías de indicadores que falten (algunos de los 47 pueden quedar sin texto — se ve explícito en `/glosario`, no se inventa)
- [ ] Autenticación para el admin en producción (o reemplazar por un panel propio) + Postgres real vía `DATABASE_URL`
- [ ] Definir dominio y despliegue (Django detrás de gunicorn/Render/Railway, frontend en Vercel)
