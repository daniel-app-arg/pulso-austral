# Pulso Austral — handoff

Dashboard + blog con indicadores de Argentina (económicos, sociales, geopolíticos).
Armado como artifact de React en claude.ai; este documento resume todo lo decidido
para retomarlo en Claude Code y convertirlo en una web real.

## Archivos de este handoff

- `pulso-austral.jsx` — el componente completo (dashboard + timeline + modal de
  gráficos + noticias), ya con la capa de conexión a Supabase armada.
- `pulso-austral-schema.sql` — esquema completo de base de datos (Postgres/Supabase),
  con las 9 categorías, RLS, vistas y seed de ejemplo.

## Identidad de marca

- **Nombre**: Pulso Austral
- **Tagline**: "El estado del país, medido."

### Paleta
| Uso | Color |
|---|---|
| Fondo (papel) | `#EDE7D9` |
| Tinta | `#1A1A17` |
| Base oscura (masthead/footer) | `#12232B` |
| Acento primario (ocre) | `#C98A2C` |
| Acento positivo (petróleo) | `#1F6F6B` |
| Acento negativo (ladrillo) | `#A23B2E` |

### Tipografía
- Titulares/editorial: **Fraunces** (serif)
- Datos/UI: **IBM Plex Sans**

## Categorías del dashboard (9 totales)

Solo 3 están completamente armadas en el artifact (macro, empleo, geo) con
indicadores y datos mock. Faltan: pobreza, producción, sector externo,
institucional, bienestar, percepción. Ya están cargadas como filas en el seed
del SQL, solo falta sumarles indicadores y conectarlas en el frontend.

## Features ya implementadas en el artifact

- Header con **dólar oficial, dólar blue y Merval** destacados + brecha cambiaria calculada
- Cinta de indicadores (ticker) con scroll continuo
- Navegación por pestañas de categoría
- Tarjetas de indicador con sparkline, delta, trend, y **link a la fuente de datos**
- Modal de gráfico expandido por indicador, con **4 granularidades** (días/semanas/meses/años) y navegación temporal hacia atrás/adelante
- Línea de tiempo de eventos con sentimiento (positivo/negativo/neutral), vista compacta y expandida con navegador de mes y resumen de conteos
- Noticias filtradas por categoría activa
- Capa de conexión a Supabase vía `fetch` nativo (sin librerías), con fallback automático a datos mock si no hay conexión

## Base de datos (ver `pulso-austral-schema.sql`)

6 tablas: `categorias`, `fuentes`, `indicadores`, `indicador_valores` (la serie
de tiempo que alimenta gráficos y timeline), `eventos_timeline`, `noticias`.
2 vistas: `ultimos_valores` (pinta las tarjetas) y `timeline_resumen_mensual`
(el cuadrito de conteos). RLS habilitado con lectura pública en todas las
tablas — la escritura queda reservada a la `service_role key` (nunca en el
frontend).

## Pendientes para la versión real (Next.js)

- [ ] Separar el componente monolítico en componentes reutilizables
- [ ] Reemplazar `fetch` directo a la REST API por el cliente `@supabase/supabase-js` (sí disponible en Next.js, a diferencia del entorno de artifacts)
- [ ] Cron job (Vercel Cron o similar) que traiga datos reales de BCRA/INDEC y los inserte en `indicador_valores` — usando la `service_role key`, no la `anon key`
- [ ] Completar los indicadores de las 6 categorías que faltan
- [ ] Proceso (manual o asistido por IA) para cargar y clasificar sentimiento de eventos del timeline y noticias
- [ ] Definir dominio (evaluamos "pulsoaustral.com" / ".com.ar" — chequear disponibilidad al momento de registrar)
