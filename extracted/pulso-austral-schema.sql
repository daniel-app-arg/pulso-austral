-- ============================================================================
-- PULSO AUSTRAL — esquema de base de datos (PostgreSQL / Supabase)
-- ============================================================================
-- Pensado para reemplazar los datos mock del artifact (CATEGORIAS, TIMELINE,
-- NOTICIAS) por datos reales. Seis tablas: fuentes, categorias, indicadores,
-- indicador_valores (la serie de tiempo que alimenta los gráficos), eventos_
-- timeline y noticias.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FUENTES: normalizada aparte porque el mismo organismo (INDEC, BCRA...)
-- se repite como fuente de varios indicadores, eventos y noticias.
-- ----------------------------------------------------------------------------
CREATE TABLE fuentes (
  id      SERIAL PRIMARY KEY,
  nombre  TEXT NOT NULL,
  url     TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- CATEGORIAS: las 9 secciones del dashboard.
-- ----------------------------------------------------------------------------
CREATE TABLE categorias (
  id      TEXT PRIMARY KEY,        -- slug: 'macro', 'empleo', etc.
  nombre  TEXT NOT NULL,
  color   TEXT NOT NULL,           -- hex, para mantener la identidad visual
  icono   TEXT,                    -- nombre del ícono lucide-react
  orden   INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- INDICADORES: catálogo/metadata de cada indicador (no los valores en sí).
-- 'destacado' marca los que van arriba de todo en el header (dólar, Merval).
-- ----------------------------------------------------------------------------
CREATE TABLE indicadores (
  id            TEXT PRIMARY KEY,  -- slug: 'inflacion_interanual', 'dolar_blue'
  categoria_id  TEXT NOT NULL REFERENCES categorias(id),
  nombre        TEXT NOT NULL,
  tipo          TEXT NOT NULL CHECK (tipo IN ('numerico', 'cualitativo')),
  unidad        TEXT,              -- '%','pb','US$ B','$'... null si es cualitativo
  destacado     BOOLEAN NOT NULL DEFAULT FALSE,
  fuente_id     INTEGER REFERENCES fuentes(id),
  orden         INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- INDICADOR_VALORES: la serie de tiempo. Un renglón por indicador+fecha+
-- granularidad. Acá vive todo lo que alimenta las tarjetas y los gráficos
-- expandidos (días/semanas/meses/años).
-- ----------------------------------------------------------------------------
CREATE TABLE indicador_valores (
  id              BIGSERIAL PRIMARY KEY,
  indicador_id    TEXT NOT NULL REFERENCES indicadores(id),
  fecha           DATE NOT NULL,
  granularidad    TEXT NOT NULL CHECK (granularidad IN ('dia', 'semana', 'mes', 'anio')),
  valor_numerico  NUMERIC,         -- para indicadores numéricos
  valor_texto     TEXT,            -- para cualitativos ("En revisión", "CCC+")
  delta_texto     TEXT,            -- ya formateado: "-42pp vs. año anterior"
  trend           TEXT CHECK (trend IN ('up', 'down', 'flat')),
  UNIQUE (indicador_id, fecha, granularidad)
);

-- ----------------------------------------------------------------------------
-- EVENTOS_TIMELINE: la línea de tiempo con referencia positiva/negativa.
-- ----------------------------------------------------------------------------
CREATE TABLE eventos_timeline (
  id            BIGSERIAL PRIMARY KEY,
  fecha         DATE NOT NULL,
  titulo        TEXT NOT NULL,
  categoria_id  TEXT NOT NULL REFERENCES categorias(id),
  sentimiento   TEXT NOT NULL CHECK (sentimiento IN ('positivo', 'negativo', 'neutral')),
  fuente_id     INTEGER REFERENCES fuentes(id)
);

-- ----------------------------------------------------------------------------
-- NOTICIAS: el blog, filtrable por categoría igual que en el artifact.
-- ----------------------------------------------------------------------------
CREATE TABLE noticias (
  id            BIGSERIAL PRIMARY KEY,
  categoria_id  TEXT NOT NULL REFERENCES categorias(id),
  kicker        TEXT,
  fecha         DATE NOT NULL,
  titulo        TEXT NOT NULL,
  bajada        TEXT,
  cuerpo        TEXT,              -- nota completa, si el blog crece más allá de la bajada
  fuente_id     INTEGER REFERENCES fuentes(id),
  publicado     BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================================
-- ÍNDICES — para que las consultas que arman el dashboard sean rápidas
-- ============================================================================
CREATE INDEX idx_valores_indicador_gran_fecha
  ON indicador_valores (indicador_id, granularidad, fecha DESC);
CREATE INDEX idx_eventos_fecha ON eventos_timeline (fecha DESC);
CREATE INDEX idx_noticias_categoria_fecha ON noticias (categoria_id, fecha DESC);

-- ============================================================================
-- VISTAS — resuelven directo en SQL las dos consultas que más se repiten
-- ============================================================================

-- Último valor cargado de cada indicador por granularidad: esto es lo que
-- pinta las tarjetas (valor, delta, trend) sin tener que calcularlo en JS.
CREATE VIEW ultimos_valores WITH (security_invoker = true) AS
SELECT DISTINCT ON (indicador_id, granularidad)
  indicador_id, granularidad, fecha, valor_numerico, valor_texto, trend, delta_texto
FROM indicador_valores
ORDER BY indicador_id, granularidad, fecha DESC;

-- Conteo de eventos positivos/negativos/neutros por mes: exactamente el
-- "cuadrito" resumen del timeline expandido.
CREATE VIEW timeline_resumen_mensual WITH (security_invoker = true) AS
SELECT
  date_trunc('month', fecha)::date AS mes,
  sentimiento,
  COUNT(*) AS cantidad
FROM eventos_timeline
GROUP BY 1, 2
ORDER BY 1 DESC;

-- ============================================================================
-- SEGURIDAD (RLS) — Supabase bloquea todo por defecto. Esto habilita lectura
-- pública (necesaria para que el frontend consulte con la clave "anon", que
-- es pública por diseño) y deja la escritura solo para el backend/servicio.
-- Las vistas de arriba usan security_invoker = true, así que heredan estas
-- mismas políticas de sus tablas base — no hace falta declarar políticas
-- para las vistas.
-- ============================================================================
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuentes ENABLE ROW LEVEL SECURITY;
ALTER TABLE indicadores ENABLE ROW LEVEL SECURITY;
ALTER TABLE indicador_valores ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE noticias ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura pública" ON categorias FOR SELECT USING (true);
CREATE POLICY "Lectura pública" ON fuentes FOR SELECT USING (true);
CREATE POLICY "Lectura pública" ON indicadores FOR SELECT USING (true);
CREATE POLICY "Lectura pública" ON indicador_valores FOR SELECT USING (true);
CREATE POLICY "Lectura pública" ON eventos_timeline FOR SELECT USING (true);
CREATE POLICY "Lectura pública" ON noticias FOR SELECT USING (publicado = true);
-- No hay políticas de INSERT/UPDATE/DELETE: eso queda reservado a la
-- "service_role key" (nunca se usa en el frontend, solo en el cron job que
-- carga los datos desde el backend).

-- ============================================================================
-- SEED — las 9 categorías completas del brief original
-- ============================================================================
INSERT INTO categorias (id, nombre, color, icono, orden) VALUES
  ('macro',          'Macroeconomía',              '#C98A2C', 'Landmark',    1),
  ('empleo',         'Empleo y trabajo',            '#1F6F6B', 'Users',       2),
  ('pobreza',        'Pobreza y desigualdad',       '#A23B2E', 'Scale',       3),
  ('produccion',     'Producción y actividad',      '#7A6A3F', 'Factory',     4),
  ('sector_externo', 'Sector externo y financiero', '#2C6E8E', 'TrendingUp',  5),
  ('institucional',  'Institucional y gobernanza',  '#5B4B8A', 'Landmark',    6),
  ('bienestar',      'Bienestar social',            '#3E7C4A', 'HeartPulse',  7),
  ('percepcion',     'Percepción y sentimiento',    '#8A5A3F', 'Gauge',       8),
  ('geo',            'Geopolítica',                 '#A23B2E', 'Globe2',      9);

INSERT INTO fuentes (nombre, url) VALUES
  ('INDEC',                 'https://www.indec.gob.ar/'),
  ('BCRA',                  'https://www.bcra.gob.ar/'),
  ('Ámbito Financiero',     'https://www.ambito.com/contenidos/riesgo-pais.html'),
  ('Ministerio de Economía','https://www.argentina.gob.ar/economia'),
  ('FMI',                   'https://www.imf.org/en/Countries/ARG'),
  ('S&P Global Ratings',    'https://www.spglobal.com/ratings/en/'),
  ('Mercosur',               'https://www.mercosur.int/');

-- Ejemplos de indicadores destacados (header) — el resto de indicadores por
-- categoría se cargan igual, uno por INSERT, con destacado = FALSE.
INSERT INTO indicadores (id, categoria_id, nombre, tipo, unidad, destacado, fuente_id, orden) VALUES
  ('dolar_oficial',        'macro', 'Dólar oficial',            'numerico', '$', TRUE,  2, 0),
  ('dolar_blue',           'macro', 'Dólar blue',                'numerico', '$', TRUE,  2, 0),
  ('merval',               'macro', 'Merval',                    'numerico', 'pts', TRUE, 3, 0),
  ('inflacion_interanual', 'macro', 'Inflación interanual',      'numerico', '%', FALSE, 1, 1),
  ('riesgo_pais',          'macro', 'Riesgo país (EMBI)',        'numerico', 'pb', FALSE, 3, 2),
  ('desempleo',            'empleo','Desempleo',                 'numerico', '%', FALSE, 1, 1),
  ('acuerdo_fmi',          'geo',   'Acuerdo con el FMI',        'cualitativo', NULL, FALSE, 5, 1);

-- Ejemplo de carga de valores mensuales para un indicador:
-- INSERT INTO indicador_valores (indicador_id, fecha, granularidad, valor_numerico, delta_texto, trend) VALUES
--   ('inflacion_interanual', '2026-09-01', 'mes', 118, '-42pp vs. año anterior', 'down');

-- Ejemplo de evento del timeline:
-- INSERT INTO eventos_timeline (fecha, titulo, categoria_id, sentimiento, fuente_id) VALUES
--   ('2026-09-07', 'Brecha cambiaria en su mínimo de 8 meses', 'macro', 'positivo', 3);
