# Pulso Austral — frontend (Next.js)

Puerto a Next.js (App Router, TypeScript) del artifact original
(`pulso-austral.jsx`), separado en componentes, conectado al backend Django
en vez de a Supabase.

## Arrancar en local

Con el backend Django corriendo en `http://127.0.0.1:8000` (ver
`../backend/README.md`):

```bash
cd frontend
npm install
npm run dev
```

Abre en http://localhost:3000. `.env.local` define `API_BASE_URL` (por
defecto `http://127.0.0.1:8000/api`).

## Estructura

- `src/app/page.tsx` — Server Component: pide los datos (`getDashboardData`)
  y renderiza `<Dashboard>`. `dynamic = 'force-dynamic'`: nunca cachea, cada
  visita refleja el último dato del backend.
- `src/app/layout.tsx`, `src/app/globals.css` — layout raíz y todo el CSS
  (clases `pa-*`), puerto 1:1 del `<style>` que tenía el artifact.
- `src/lib/`
  - `types.ts` — DTOs de la API + modelos de vista (`CategoriaVM`, `IndicadorVM`, etc.)
  - `api.ts` — cliente fetch al backend Django (reemplaza `supaFetch`)
  - `transform.ts` — API → modelos de vista (puerto de `construirCategoriasDesdeDB` y compañía)
  - `mocks.ts` + `get-dashboard-data.ts` — si el backend no responde, cae a datos de ejemplo (mismo principio que tenía el artifact con Supabase)
  - `format.ts` — helpers de fecha (`MESES`, `fechaCorta`, etc.)
- `src/components/` — un componente por pieza de UI: `Masthead`, `NavCategorias`,
  `PanelIndicadores` + `IndicadorCard`, `TimelineSection`, `NoticiasSection`,
  `IndicadorModal` + `ChartExpandido`, `Sparkline`, `TrendIcon`, `Footer`,
  `icon-map`, `PulsoIndexBanner`. `Dashboard.tsx` los orquesta y mantiene
  el estado (categoría activa, modal abierto). `SiteNav` + `PageHeader` son el
  encabezado liviano (título + navegación) que comparten las páginas
  secundarias; `Masthead` (home) también incluye `SiteNav`.

## Páginas secundarias

- **`/medios`** (`app/medios/page.tsx`) — directorio de medios de
  comunicación con una escala visual de orientación política
  (`OrientacionScale`: puntos en una recta izquierda-derecha, sin colores
  por bloque a propósito, para no sugerir un juicio de valor) y una breve
  justificación de cada caracterización. Datos vía `lib/get-medios.ts`.
- **`/gobiernos`** (`app/gobiernos/page.tsx`) — comparativa de todos los
  indicadores por mandato presidencial (4 años). El Server Component
  (`lib/get-gobiernos-comparativa.ts`) trae la lista de gobiernos y el
  resumen de **cada uno** de una sola vez; el Client Component
  (`GobiernosComparativa.tsx`) solo cambia cuál mostrar — sin fetches
  nuevos al hacer clic, porque son pocos gobiernos y el payload de cada
  resumen es chico. Los indicadores sin datos en el rango muestran "sin
  datos cargados para este período" en vez de desaparecer.
- **`/glosario`** (`app/glosario/page.tsx`) — qué mide y cómo se calcula
  cada indicador, agrupado por categoría (`lib/get-glosario.ts`, reusa
  `/api/indicadores/`, sin endpoint nuevo). Si a un indicador todavía no
  se le cargó `metodologia`, lo dice explícito ("Metodología todavía no
  documentada") en vez de mostrar un texto inventado.

## Noticias

`NoticiasSection.tsx` ahora muestra, cuando existe, el medio y el link a
la nota original ("fuente: Infobae ↗") debajo de la bajada — viene de
`Noticia.medio`/`Noticia.url` en el backend. El link puede quedar roto con
el tiempo; el título y la bajada (que sí persisten siempre) no dependen de
que siga vivo. Ver `../backend/README.md` → "Noticias reales" para cómo se
cargó el primer fill (19 noticias verificadas por búsqueda web, no
inventadas).

## Índice general

`PulsoIndexBanner.tsx`, arriba de todo en el home (antes incluso del
`Masthead`) — el score 0-100 de `/api/pulso-index/`, con un botón "¿Cómo
se calcula?" que despliega la metodología completa y el detalle de los 31
indicadores considerados (icono verde/rojo/gris = mejora/empeora/sin
cambio). A diferencia del resto del dashboard, si el backend no responde
el banner simplemente no se muestra (`lib/get-pulso-index.ts` devuelve
`null`) — no tendría sentido mostrar un score inventado. Metodología
completa (qué entra, qué se excluye y por qué) documentada en
`../backend/README.md` y en `pulso_index.py`.

## Identidad visual (logo/favicon)

El isotipo es el Sol de Mayo atravesado por una línea de pulso/electrocardiograma
— elegido entre 6 direcciones exploradas con el skill de diseño (historial
completo, con el resto de las opciones archivadas en una segunda página,
en el canvas de diseño publicado). El disco es opaco, así que el mismo SVG
sirve sobre fondo claro u oscuro sin variantes.

- `branding/logo/pulso-austral-mark.svg` (raíz del repo, fuera de `frontend/`)
  — el archivo maestro. Cualquier otro asset del logo sale de acá.
- `src/app/icon.svg` — favicon (convención de Next.js: se sirve y referencia
  solo, sin tocar `layout.tsx`).
- `src/app/apple-icon.png` (180×180) — ícono para iOS, con fondo sólido
  `--dark` (un PNG transparente no se ve bien en la pantalla de inicio).
  Generado desde `branding/logo/apple-icon-source.svg` con
  `branding/logo/rasterize.mjs` (usa `sharp`, ya en `node_modules`).
- `src/components/LogoMark.tsx` — el isotipo como componente React, usado
  junto al wordmark en `Masthead` (home) y `PageHeader` (páginas secundarias).

## Diferencias a propósito con el artifact original

- El **ticker** superior ya no es un array fijo: se arma dinámicamente a
  partir de 6 indicadores elegidos (`inflacion_interanual`, `riesgo_pais`,
  `merval`, `reservas_bcra`, `emae`, `desempleo`) usando el último valor real.
- La **brecha cambiaria** la calcula el backend (`/api/destacados/`), no el frontend.
- El modal de gráfico solo muestra las granularidades que tengan datos
  (hoy: `Meses` y `Años` para todo lo numérico salvo destacados del header;
  `Días`/`Semanas` quedan pendientes de una fuente real).

## Pendiente

- [ ] Reemplazar valores ilustrativos del backend por datos reales (ver `../backend/README.md`)
- [ ] Cargar granularidad `dia`/`semana` cuando haya una fuente real (BCRA/INDEC)
- [ ] Cargar series pre-2017 para que `/gobiernos` tenga datos de los mandatos más viejos
- [ ] Deploy (Vercel para el frontend, backend Django detrás de Render/Railway + Postgres)
- [ ] Definir dominio
