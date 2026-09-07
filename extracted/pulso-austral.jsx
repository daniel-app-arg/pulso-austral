import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Landmark,
  Users,
  Globe2,
  Newspaper,
  Clock,
  ChevronLeft,
  ChevronRight,
  Scale,
  Factory,
  HeartPulse,
  Gauge,
} from "lucide-react";

// ---------------------------------------------------------------------------
// CONEXIÓN A SUPABASE — reemplazá estos dos valores por los de tu proyecto
// (Project Settings → API en el panel de Supabase). La "anon key" es pública
// por diseño: la seguridad real la da Row Level Security (ver el .sql), no
// esconder esta clave.
// ---------------------------------------------------------------------------
const SUPABASE_URL = "https://TU-PROYECTO.supabase.co";
const SUPABASE_ANON_KEY = "TU-ANON-KEY";
const SUPABASE_CONFIGURADO = !SUPABASE_URL.includes("TU-PROYECTO");

async function supaFetch(path) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
  });
  if (!res.ok) throw new Error(`Supabase respondió ${res.status}`);
  return res.json();
}

const ICONOS_DB = { Landmark, Users, Globe2, Scale, Factory, TrendingUp, HeartPulse, Gauge };

// ---------------------------------------------------------------------------
// MOCK DATA — cuando esto se convierta en una web real, cada bloque de abajo
// se reemplaza por un fetch a la fuente correspondiente (BCRA, INDEC, REM,
// agencias de noticias, etc.). La forma de los objetos ya está pensada para
// eso.
// ---------------------------------------------------------------------------

const DOLARES = {
  oficial: { valor: 1042, delta: 0.4 },
  blue: { valor: 1380, delta: -0.7 },
};

const MERVAL = { valor: 1852340, delta: 1.8 };

const TICKER = [
  { label: "Inflación mensual", valor: "3.1%", trend: "down" },
  { label: "Riesgo país", valor: "612 pb", trend: "down" },
  { label: "Merval", valor: "+1.8%", trend: "up" },
  { label: "Reservas BCRA", valor: "US$ 29.400 M", trend: "up" },
  { label: "EMAE", valor: "+0.6%", trend: "up" },
  { label: "Desempleo", valor: "7.2%", trend: "flat" },
];

const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

// Genera etiquetas de los últimos n meses, terminando en septiembre 2026
// (la fecha "actual" de referencia de esta demo), formato corto "sep-26".
function periodosHastaHoy(n) {
  const base = new Date(2026, 8, 1);
  const out = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(base.getFullYear(), base.getMonth() - i, 1);
    out.push(`${MESES[d.getMonth()].slice(0, 3)}-${String(d.getFullYear()).slice(2)}`);
  }
  return out;
}
const PERIODOS_14M = periodosHastaHoy(14);
function serie(valores) {
  return PERIODOS_14M.map((label, i) => ({ label, valor: valores[i] }));
}

// -- Generación de series sintéticas para días/semanas, a partir de la curva
// mensual ya cargada a mano. Cuando esto se conecte a datos reales, cada
// granularidad se reemplaza por su propio fetch (BCRA/INDEC suelen publicar
// series diarias o semanales para varios de estos indicadores).
function hashTexto(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return h;
}
function pseudoRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
}
function redondear(v, decimales) {
  const f = Math.pow(10, decimales);
  return Math.round(v * f) / f;
}
// Interpola n puntos a lo largo de la curva mensual (14 valores) y les suma
// una pequeña variación aleatoria, manteniendo el último punto exacto.
function densificar(mensual, n, volatilidad, seedTxt, decimales) {
  const rand = pseudoRandom(hashTexto(seedTxt));
  const m = mensual.length;
  const out = [];
  for (let i = 0; i < n; i++) {
    const pos = (i / (n - 1)) * (m - 1);
    const i0 = Math.floor(pos);
    const i1 = Math.min(m - 1, i0 + 1);
    const base = mensual[i0] + (mensual[i1] - mensual[i0]) * (pos - i0);
    const ruido = (rand() - 0.5) * 2 * volatilidad;
    out.push(i === n - 1 ? mensual[m - 1] : redondear(base + ruido, decimales));
  }
  return out;
}
function etiquetasDias(n) {
  const base = new Date(2026, 8, 7);
  const out = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(base);
    d.setDate(d.getDate() - i);
    out.push(`${String(d.getDate()).padStart(2, "0")} ${MESES[d.getMonth()].slice(0, 3)}`);
  }
  return out;
}
function etiquetasSemanas(n) {
  const base = new Date(2026, 8, 7);
  const out = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(base);
    d.setDate(d.getDate() - i * 7);
    out.push(`${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`);
  }
  return out;
}
function etiquetasAnios(n) {
  const out = [];
  for (let i = n - 1; i >= 0; i--) out.push(String(2026 - i));
  return out;
}
const LABELS_DIAS = etiquetasDias(90);
const LABELS_SEMANAS = etiquetasSemanas(52);
const LABELS_ANIOS = etiquetasAnios(10);

// valoresMensuales: los 14 puntos ya cargados a mano.
// valoresAnuales: 10 puntos (una década) cargados a mano aparte, porque a
// esa escala los movimientos importantes no se ven bien "interpolando" el
// último año y medio.
function construirGranularidades(valoresMensuales, valoresAnuales, volatilidad, decimales, seedTxt) {
  const dias = densificar(valoresMensuales, 90, volatilidad, seedTxt + "-d", decimales);
  const semanas = densificar(valoresMensuales, 52, volatilidad * 1.4, seedTxt + "-s", decimales);
  return {
    dias: LABELS_DIAS.map((label, i) => ({ label, valor: dias[i] })),
    semanas: LABELS_SEMANAS.map((label, i) => ({ label, valor: semanas[i] })),
    meses: serie(valoresMensuales),
    anios: LABELS_ANIOS.map((label, i) => ({ label, valor: valoresAnuales[i] })),
  };
}

const CATEGORIAS = [
  {
    id: "macro",
    nombre: "Macroeconomía",
    icon: Landmark,
    color: "#C98A2C",
    indicadores: [
      {
        label: "Inflación interanual", valor: "118%", delta: "-42pp vs. año anterior", trend: "down",
        fuente: { nombre: "INDEC", url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31" },
        historias: construirGranularidades(
          [268, 245, 225, 205, 188, 172, 158, 146, 136, 128, 122, 120, 119, 118],
          [25, 48, 54, 36, 51, 95, 140, 190, 230, 118],
          2.5, 1, "inflacion"
        ),
      },
      {
        label: "Riesgo país (EMBI)", valor: "612 pb", delta: "-38pb en el mes", trend: "down",
        fuente: { nombre: "Ámbito Financiero", url: "https://www.ambito.com/contenidos/riesgo-pais.html" },
        historias: construirGranularidades(
          [950, 910, 880, 850, 820, 790, 760, 730, 700, 670, 650, 635, 620, 612],
          [450, 550, 800, 1500, 1700, 2000, 1900, 1600, 900, 612],
          12, 0, "riesgopais"
        ),
      },
      {
        label: "Reservas netas BCRA", valor: "US$ 29.400 M", delta: "+US$1.200M en el mes", trend: "up",
        fuente: { nombre: "BCRA", url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp" },
        historias: construirGranularidades(
          [18.0, 18.5, 19.2, 20.0, 20.8, 21.5, 22.3, 23.1, 24.0, 24.9, 25.8, 27.0, 28.2, 29.4],
          [10, 8, 5, 3, -3, -5, 2, 10, 18, 29.4],
          0.3, 1, "reservas"
        ),
      },
      {
        label: "Resultado fiscal primario", valor: "+0.3% PBI", delta: "superávit 8vo mes", trend: "up",
        fuente: { nombre: "Ministerio de Economía", url: "https://www.argentina.gob.ar/economia" },
        historias: construirGranularidades(
          [-1.8, -1.5, -1.3, -1.0, -0.8, -0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.15, 0.25, 0.3],
          [-4.2, -3.8, -3.5, -6.5, -3.0, -2.4, -1.5, -0.5, -0.2, 0.3],
          0.08, 2, "fiscal"
        ),
      },
    ],
  },
  {
    id: "empleo",
    nombre: "Empleo y trabajo",
    icon: Users,
    color: "#1F6F6B",
    indicadores: [
      {
        label: "Desempleo", valor: "7.2%", delta: "+0.3pp vs. trim. anterior", trend: "up",
        fuente: { nombre: "INDEC", url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58" },
        historias: construirGranularidades(
          [6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, 7.0, 7.1, 7.2],
          [8.3, 9.1, 9.8, 11.5, 8.7, 7.1, 6.2, 6.9, 7.5, 7.2],
          0.15, 1, "desempleo"
        ),
      },
      {
        label: "Salario real", valor: "-1.4%", delta: "interanual", trend: "down",
        fuente: { nombre: "INDEC", url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31" },
        historias: construirGranularidades(
          [-6.5, -6.0, -5.5, -5.0, -4.5, -4.0, -3.5, -3.0, -2.6, -2.2, -1.9, -1.7, -1.6, -1.4],
          [3.0, -2.0, -5.7, -2.5, 4.0, -3.0, -12.0, -8.0, -4.0, -1.4],
          0.3, 1, "salario"
        ),
      },
      {
        label: "Empleo informal", valor: "41.8%", delta: "sin cambios", trend: "flat",
        fuente: { nombre: "INDEC", url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58" },
        historias: construirGranularidades(
          [42.5, 42.3, 42.1, 42.0, 41.9, 42.0, 41.9, 41.8, 41.9, 41.8, 41.9, 41.8, 41.9, 41.8],
          [33.5, 34.0, 35.1, 36.8, 36.0, 35.5, 38.0, 40.5, 42.0, 41.8],
          0.1, 1, "informalidad"
        ),
      },
      {
        label: "Canasta básica total", valor: "$1.150.000", delta: "familia tipo, +2.1% mensual", trend: "up",
        fuente: { nombre: "INDEC", url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-46-153" },
        historias: construirGranularidades(
          [850000, 880000, 910000, 940000, 970000, 1000000, 1030000, 1060000, 1080000, 1100000, 1115000, 1130000, 1140000, 1150000],
          [18000, 25000, 38000, 55000, 95000, 190000, 420000, 750000, 980000, 1150000],
          4000, 0, "canasta"
        ),
      },
    ],
  },
  {
    id: "geo",
    nombre: "Geopolítica",
    icon: Globe2,
    color: "#A23B2E",
    indicadores: [
      { label: "Acuerdo con el FMI", valor: "En revisión", delta: "próximo desembolso: oct.", trend: "flat", historias: null, fuente: { nombre: "FMI", url: "https://www.imf.org/en/Countries/ARG" } },
      { label: "Calificación soberana", valor: "CCC+", delta: "perspectiva positiva (S&P)", trend: "up", historias: null, fuente: { nombre: "S&P Global Ratings", url: "https://www.spglobal.com/ratings/en/" } },
      { label: "Swap con China", valor: "US$ 5.000 M activos", delta: "sin cambios en el trimestre", trend: "flat", historias: null, fuente: { nombre: "BCRA", url: "https://www.bcra.gob.ar/" } },
      { label: "Mercosur–UE", valor: "Acuerdo firmado", delta: "pendiente ratificación", trend: "up", historias: null, fuente: { nombre: "Mercosur", url: "https://www.mercosur.int/" } },
    ],
  },
];

const NOTICIAS = [
  {
    categoria: "macro",
    kicker: "Economía",
    fecha: "7 de septiembre",
    titulo: "La brecha cambiaria se achica por tercera semana consecutiva",
    bajada:
      "El spread entre el dólar oficial y el blue cayó a su nivel más bajo en ocho meses, impulsado por la mayor oferta de divisas del agro.",
  },
  {
    categoria: "macro",
    kicker: "Economía",
    fecha: "4 de septiembre",
    titulo: "El Banco Central acumuló reservas por cuarta semana al hilo",
    bajada:
      "Las compras se explican por la liquidación del agro y una mayor demanda de pesos estacional.",
  },
  {
    categoria: "empleo",
    kicker: "Trabajo",
    fecha: "6 de septiembre",
    titulo: "El salario real mostró la primera mejora mensual del año",
    bajada:
      "Paritarias por encima de la inflación en tres sectores clave frenaron, por ahora, la caída del poder adquisitivo.",
  },
  {
    categoria: "empleo",
    kicker: "Trabajo",
    fecha: "2 de septiembre",
    titulo: "Crece el empleo registrado en la construcción",
    bajada:
      "Es el tercer mes de recuperación tras la fuerte caída del año pasado, según datos del Ministerio de Trabajo.",
  },
  {
    categoria: "geo",
    kicker: "Geopolítica",
    fecha: "6 de septiembre",
    titulo: "El Gobierno negocia un nuevo tramo de desembolsos con el FMI",
    bajada:
      "La misión del organismo llega a Buenos Aires la semana próxima para revisar el cumplimiento de las metas fiscales del segundo semestre.",
  },
  {
    categoria: "geo",
    kicker: "Geopolítica",
    fecha: "3 de septiembre",
    titulo: "Avanza la ratificación del acuerdo Mercosur–Unión Europea",
    bajada:
      "Cancillería espera que el tratado esté listo para su firma definitiva antes de fin de año.",
  },
];

const TIMELINE = [
  { fecha: "2026-09-07", titulo: "Brecha cambiaria en su mínimo de 8 meses", sentimiento: "positivo", categoria: "macro" },
  { fecha: "2026-09-06", titulo: "Salario real mejora por primera vez en el año", sentimiento: "positivo", categoria: "empleo" },
  { fecha: "2026-09-06", titulo: "Misión del FMI llega para revisar metas fiscales", sentimiento: "neutral", categoria: "geo" },
  { fecha: "2026-09-04", titulo: "BCRA acumula reservas por cuarta semana consecutiva", sentimiento: "positivo", categoria: "macro" },
  { fecha: "2026-09-03", titulo: "Avanza la ratificación del acuerdo Mercosur–UE", sentimiento: "positivo", categoria: "geo" },
  { fecha: "2026-09-02", titulo: "Sube el empleo registrado en la construcción", sentimiento: "positivo", categoria: "empleo" },
  { fecha: "2026-08-29", titulo: "Suba en la tasa de desempleo del segundo trimestre", sentimiento: "negativo", categoria: "empleo" },
  { fecha: "2026-08-27", titulo: "S&P sube la perspectiva de la calificación soberana", sentimiento: "positivo", categoria: "geo" },
  { fecha: "2026-08-22", titulo: "El dólar blue subió tres ruedas seguidas", sentimiento: "negativo", categoria: "macro" },
  { fecha: "2026-08-18", titulo: "Cae la producción industrial por segundo mes", sentimiento: "negativo", categoria: "macro" },
  { fecha: "2026-08-14", titulo: "Tensión comercial por trabas para importar insumos", sentimiento: "negativo", categoria: "geo" },
  { fecha: "2026-08-09", titulo: "Se recupera el poder de compra del salario mínimo", sentimiento: "positivo", categoria: "empleo" },
  { fecha: "2026-08-05", titulo: "El Merval marcó un nuevo máximo en pesos", sentimiento: "positivo", categoria: "macro" },
  { fecha: "2026-07-30", titulo: "El Gobierno cerró el acuerdo técnico con el FMI", sentimiento: "positivo", categoria: "geo" },
  { fecha: "2026-07-24", titulo: "Aumentó la informalidad laboral en el segundo trimestre", sentimiento: "negativo", categoria: "empleo" },
  { fecha: "2026-07-19", titulo: "Moody's mantuvo la calificación soberana sin cambios", sentimiento: "neutral", categoria: "geo" },
  { fecha: "2026-07-11", titulo: "La inflación núcleo volvió a acelerarse", sentimiento: "negativo", categoria: "macro" },
  { fecha: "2026-07-03", titulo: "Se creó empleo privado por primera vez en el año", sentimiento: "positivo", categoria: "empleo" },
];

// MESES ya está definido arriba, junto a CATEGORIAS.
function mesKey(fechaISO) {
  const [y, m] = fechaISO.split("-");
  return `${y}-${m}`;
}

// ---------------------------------------------------------------------------
// TRANSFORMACIÓN: de las filas planas que devuelve Supabase a la misma forma
// que ya usan los mocks de arriba (CATEGORIAS/TIMELINE/NOTICIAS). Así el
// resto del componente no necesita saber si el dato vino de la base o no.
// ---------------------------------------------------------------------------
const GRAN_DB_A_JS = { dia: "dias", semana: "semanas", mes: "meses", anio: "anios" };

function etiquetaDesdeDB(fechaISO, granularidad) {
  const [y, m, d] = fechaISO.split("-").map(Number);
  if (granularidad === "anio") return String(y);
  if (granularidad === "mes") return `${MESES[m - 1].slice(0, 3)}-${String(y).slice(2)}`;
  return `${String(d).padStart(2, "0")} ${MESES[m - 1].slice(0, 3)}`;
}

function fechaLargaDesdeDB(fechaISO) {
  const [, m, d] = fechaISO.split("-").map(Number);
  return `${d} de ${MESES[m - 1]}`;
}

function construirIndicadorDesdeDB(ind, valores) {
  const propios = valores.filter((v) => v.indicador_id === ind.id);
  const porGranularidad = { dias: [], semanas: [], meses: [], anios: [] };
  propios.forEach((v) => {
    const clave = GRAN_DB_A_JS[v.granularidad];
    if (!clave) return;
    porGranularidad[clave].push({
      label: etiquetaDesdeDB(v.fecha, v.granularidad),
      valor: v.valor_numerico ?? v.valor_texto,
      delta: v.delta_texto,
      trend: v.trend,
    });
  });
  const ultimo = porGranularidad.meses[porGranularidad.meses.length - 1] || porGranularidad.dias[porGranularidad.dias.length - 1];
  return {
    label: ind.nombre,
    valor: ind.tipo === "cualitativo" ? String(ultimo?.valor ?? "—") : `${ultimo?.valor ?? "—"}${ind.unidad ? " " + ind.unidad : ""}`,
    delta: ultimo?.delta || "",
    trend: ultimo?.trend || "flat",
    fuente: ind.fuentes ? { nombre: ind.fuentes.nombre, url: ind.fuentes.url } : null,
    historias: ind.tipo === "numerico" ? porGranularidad : null,
  };
}

function construirCategoriasDesdeDB({ categorias, indicadores, valores }) {
  return categorias.map((c) => ({
    id: c.id,
    nombre: c.nombre,
    color: c.color,
    icon: ICONOS_DB[c.icono] || Landmark,
    indicadores: indicadores.filter((i) => i.categoria_id === c.id).map((i) => construirIndicadorDesdeDB(i, valores)),
  }));
}

function construirTimelineDesdeDB({ eventos }) {
  return eventos.map((e) => ({ fecha: e.fecha, titulo: e.titulo, sentimiento: e.sentimiento, categoria: e.categoria_id }));
}

function construirNoticiasDesdeDB({ noticias }) {
  return noticias.map((n) => ({
    categoria: n.categoria_id,
    kicker: n.kicker,
    fecha: fechaLargaDesdeDB(n.fecha),
    titulo: n.titulo,
    bajada: n.bajada,
  }));
}

function construirDestacadosDesdeDB({ indicadores, valores }) {
  const valorDiaMasReciente = (indId) => {
    const filas = valores.filter((v) => v.indicador_id === indId && v.granularidad === "dia");
    return filas[filas.length - 1];
  };
  const oficial = valorDiaMasReciente("dolar_oficial");
  const blue = valorDiaMasReciente("dolar_blue");
  const merval = valorDiaMasReciente("merval");
  return {
    dolares: {
      oficial: { valor: oficial?.valor_numerico ?? DOLARES.oficial.valor, delta: parseFloat(oficial?.delta_texto) || 0 },
      blue: { valor: blue?.valor_numerico ?? DOLARES.blue.valor, delta: parseFloat(blue?.delta_texto) || 0 },
    },
    merval: { valor: merval?.valor_numerico ?? MERVAL.valor, delta: parseFloat(merval?.delta_texto) || 0 },
  };
}

function TrendIcon({ trend, size = 14 }) {
  if (trend === "up") return <TrendingUp size={size} color="#1F6F6B" strokeWidth={2.5} />;
  if (trend === "down") return <TrendingDown size={size} color="#A23B2E" strokeWidth={2.5} />;
  return <Minus size={size} color="#8A8371" strokeWidth={2.5} />;
}

function sentimentTrend(sentimiento) {
  if (sentimiento === "positivo") return "up";
  if (sentimiento === "negativo") return "down";
  return "flat";
}

function fechaCorta(fechaISO) {
  const [, m, d] = fechaISO.split("-");
  return `${parseInt(d, 10)} ${MESES[parseInt(m, 10) - 1].slice(0, 3)}`;
}

function Sparkline({ data, color }) {
  if (!data) return null;
  const w = 88;
  const h = 28;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} style={{ display: "block" }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChartExpandido({ data, color }) {
  const w = 600;
  const h = 190;
  const padX = 20;
  const padY = 14;
  const valores = data.map((d) => d.valor);
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const range = max - min || 1;
  const stepX = data.length > 1 ? (w - padX * 2) / (data.length - 1) : 0;
  const puntos = data.map((d, i) => ({
    x: padX + i * stepX,
    y: padY + (h - padY * 2) * (1 - (d.valor - min) / range),
    ...d,
  }));
  const pathD = puntos.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h + 24}`} width="100%" style={{ display: "block" }}>
      <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      {puntos.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r="3.5" fill="white" stroke={color} strokeWidth="2" />
          <text x={p.x} y={h + 16} textAnchor="middle" fontSize="11" fill="#5B5648">
            {p.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

export default function PulsoAustral() {
  const [activeCat, setActiveCat] = useState(CATEGORIAS[0].id);
  const [loaded, setLoaded] = useState(false);
  const [timelineExpandido, setTimelineExpandido] = useState(false);
  const [mesIdx, setMesIdx] = useState(0);
  const [indicadorExpandido, setIndicadorExpandido] = useState(null);
  const [ventanaOffset, setVentanaOffset] = useState(0);
  const [granularidad, setGranularidad] = useState("meses");
  const [datosDB, setDatosDB] = useState(null);
  const [estadoConexion, setEstadoConexion] = useState(SUPABASE_CONFIGURADO ? "cargando" : "demo");
  const VENTANAS = { dias: 30, semanas: 26, meses: 12, anios: 10 };
  const VENTANA = VENTANAS[granularidad];
  const GRANULARIDADES = [
    { id: "dias", nombre: "Días" },
    { id: "semanas", nombre: "Semanas" },
    { id: "meses", nombre: "Meses" },
    { id: "anios", nombre: "Años" },
  ];

  function abrirIndicador(ind, color) {
    setIndicadorExpandido({ ...ind, color });
    setVentanaOffset(0);
    setGranularidad("meses");
  }

  function cambiarGranularidad(g) {
    setGranularidad(g);
    setVentanaOffset(0);
  }
  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 60);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!SUPABASE_CONFIGURADO) return;
    (async () => {
      try {
        const [categoriasDB, indicadoresDB, valoresDB, eventosDB, noticiasDB] = await Promise.all([
          supaFetch("categorias?select=*&order=orden.asc"),
          supaFetch("indicadores?select=*,fuentes(nombre,url)&order=orden.asc"),
          supaFetch("indicador_valores?select=*&order=fecha.asc"),
          supaFetch("eventos_timeline?select=*,fuentes(nombre,url)&order=fecha.desc"),
          supaFetch("noticias?select=*,fuentes(nombre,url)&order=fecha.desc&publicado=eq.true"),
        ]);
        setDatosDB({ categorias: categoriasDB, indicadores: indicadoresDB, valores: valoresDB, eventos: eventosDB, noticias: noticiasDB });
        setEstadoConexion("conectado");
      } catch (err) {
        console.warn("No se pudo conectar a Supabase, mostrando datos de ejemplo:", err);
        setEstadoConexion("error");
      }
    })();
  }, []);

  // Si Supabase está configurado y respondió bien, usamos esos datos.
  // Si no, seguimos mostrando los mocks de arriba — el dashboard nunca
  // se rompe por falta de conexión.
  const usarDB = estadoConexion === "conectado" && datosDB;
  const categoriasActivas = usarDB ? construirCategoriasDesdeDB(datosDB) : CATEGORIAS;
  const timelineActivo = usarDB ? construirTimelineDesdeDB(datosDB) : TIMELINE;
  const noticiasActivas = usarDB ? construirNoticiasDesdeDB(datosDB) : NOTICIAS;
  const destacadosActivos = usarDB ? construirDestacadosDesdeDB(datosDB) : { dolares: DOLARES, merval: MERVAL };

  const brecha = (
    ((destacadosActivos.dolares.blue.valor - destacadosActivos.dolares.oficial.valor) / destacadosActivos.dolares.oficial.valor) *
    100
  ).toFixed(0);

  const cat = categoriasActivas.find((c) => c.id === activeCat) || categoriasActivas[0];
  const noticiasFiltradas = noticiasActivas.filter((n) => n.categoria === activeCat);

  const timelineOrdenado = [...timelineActivo].sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
  const timelineReciente = timelineOrdenado.slice(0, 6);

  const mesesDisponibles = Array.from(new Set(timelineActivo.map((ev) => mesKey(ev.fecha))))
    .sort()
    .reverse()
    .map((key) => {
      const [y, m] = key.split("-");
      return { key, label: `${MESES[parseInt(m, 10) - 1]} ${y}` };
    });
  const mesActual = mesesDisponibles[mesIdx];
  const eventosDelMes = timelineOrdenado.filter((ev) => mesKey(ev.fecha) === mesActual?.key);
  const resumenMes = eventosDelMes.reduce(
    (acc, ev) => {
      acc[ev.sentimiento] = (acc[ev.sentimiento] || 0) + 1;
      return acc;
    },
    { positivo: 0, negativo: 0, neutral: 0 }
  );

  let ventanaDatos = [];
  let rangoLabel = "";
  if (indicadorExpandido?.historias) {
    const h = indicadorExpandido.historias[granularidad];
    const fin = h.length - ventanaOffset;
    const inicio = Math.max(0, fin - VENTANA);
    ventanaDatos = h.slice(inicio, fin);
    rangoLabel = `${ventanaDatos[0]?.label} — ${ventanaDatos[ventanaDatos.length - 1]?.label}`;
  }
  const today = new Date().toLocaleDateString("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div className="pa-root">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

        .pa-root {
          --paper: #EDE7D9;
          --ink: #1A1A17;
          --ink-soft: #5B5648;
          --dark: #12232B;
          --ochre: #C98A2C;
          --teal: #1F6F6B;
          --brick: #A23B2E;
          --line: #D8D0BC;
          font-family: 'IBM Plex Sans', sans-serif;
          background: var(--paper);
          color: var(--ink);
          min-height: 100%;
          width: 100%;
        }
        .pa-serif { font-family: 'Fraunces', serif; }

        .pa-masthead {
          background: var(--dark);
          color: var(--paper);
          padding: 28px 24px 0 24px;
        }
        .pa-masthead-top {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          max-width: 980px;
          margin: 0 auto;
          flex-wrap: wrap;
          gap: 8px;
        }
        .pa-title {
          font-size: 30px;
          font-weight: 600;
          letter-spacing: 0.2px;
          margin: 0;
        }
        .pa-tagline {
          color: #A9BBC0;
          font-size: 13px;
          margin-top: 2px;
        }
        .pa-date {
          color: #A9BBC0;
          font-size: 13px;
          text-transform: capitalize;
        }
        .pa-estado-conexion {
          display: block;
          text-transform: none;
          font-size: 11px;
          margin-top: 2px;
          text-align: right;
        }
        .pa-estado-conectado { color: #6FBFA8; }
        .pa-estado-cargando { color: #A9BBC0; }
        .pa-estado-demo, .pa-estado-error { color: #C9A96E; }

        .pa-dollars {
          max-width: 980px;
          margin: 20px auto 0 auto;
          display: grid;
          grid-template-columns: 1fr 1fr 1fr auto;
          gap: 0;
          border-top: 1px solid #2A3D45;
          opacity: ${loaded ? 1 : 0};
          transform: translateY(${loaded ? "0" : "6px"});
          transition: opacity 0.5s ease, transform 0.5s ease;
        }
        .pa-dollar-block {
          padding: 16px 20px 16px 0;
          border-right: 1px solid #2A3D45;
        }
        .pa-dollar-block:last-of-type { border-right: none; }
        .pa-dollar-label {
          font-size: 12px;
          color: #A9BBC0;
          margin-bottom: 4px;
        }
        .pa-dollar-value {
          font-family: 'Fraunces', serif;
          font-size: 34px;
          font-weight: 500;
          line-height: 1;
        }
        .pa-dollar-delta {
          font-size: 12px;
          margin-top: 6px;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .pa-brecha {
          padding: 16px 0 16px 20px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          min-width: 100px;
        }
        .pa-brecha-value {
          font-size: 22px;
          font-weight: 600;
          color: var(--ochre);
        }
        .pa-brecha-label {
          font-size: 11px;
          color: #A9BBC0;
        }
        @media (max-width: 640px) {
          .pa-dollars { grid-template-columns: 1fr 1fr; }
          .pa-brecha { grid-column: span 2; flex-direction: row; align-items: baseline; gap: 8px; padding-left: 0; border-top: 1px solid #2A3D45; }
        }

        .pa-ticker-wrap {
          max-width: 980px;
          margin: 0 auto;
          overflow: hidden;
          border-top: 1px solid #2A3D45;
          margin-top: 16px;
        }
        .pa-ticker {
          display: flex;
          gap: 36px;
          white-space: nowrap;
          padding: 10px 0;
          animation: pa-scroll 28s linear infinite;
          width: max-content;
        }
        @keyframes pa-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        .pa-ticker-item {
          font-size: 12.5px;
          color: #D8D0BC;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .pa-ticker-item b { color: var(--paper); font-weight: 600; }

        .pa-nav {
          max-width: 980px;
          margin: 0 auto;
          display: flex;
          gap: 4px;
          padding: 18px 24px 0 24px;
          flex-wrap: wrap;
        }
        .pa-nav-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          border: 1px solid var(--line);
          border-bottom: none;
          background: transparent;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 13.5px;
          font-weight: 500;
          color: var(--ink-soft);
          cursor: pointer;
          border-radius: 3px 3px 0 0;
        }
        .pa-nav-btn.active {
          background: white;
          color: var(--ink);
        }

        .pa-panel {
          max-width: 980px;
          margin: 0 auto;
          background: white;
          border: 1px solid var(--line);
          padding: 22px 24px;
        }
        .pa-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1px;
          background: var(--line);
          border: 1px solid var(--line);
          margin-top: 4px;
        }
        @media (min-width: 640px) {
          .pa-grid { grid-template-columns: repeat(4, 1fr); }
        }
        .pa-card {
          background: white;
          padding: 16px 16px 14px 16px;
          border-left: 3px solid var(--cat-color, var(--ochre));
        }
        .pa-card-clickable {
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .pa-card-clickable:hover {
          background: #FAF7EF;
        }
        .pa-card-label {
          font-size: 12px;
          color: var(--ink-soft);
          margin-bottom: 6px;
        }
        .pa-card-value {
          font-family: 'Fraunces', serif;
          font-size: 22px;
          font-weight: 500;
        }
        .pa-card-delta {
          font-size: 11.5px;
          color: var(--ink-soft);
          margin-top: 6px;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .pa-card-spark { margin-top: 8px; }
        .pa-card-fuente {
          display: block;
          margin-top: 8px;
          font-size: 10.5px;
          color: var(--ink-soft);
          text-decoration: none;
        }
        .pa-card-fuente:hover {
          color: var(--ochre);
          text-decoration: underline;
        }

        .pa-section-title {
          max-width: 980px;
          margin: 40px auto 0 auto;
          padding: 0 24px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-family: 'Fraunces', serif;
          font-size: 20px;
          font-weight: 500;
        }

        .pa-timeline {
          max-width: 980px;
          margin: 14px auto 0 auto;
          padding: 0 24px;
        }
        .pa-timeline-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 9px 0;
          border-left: 2px solid var(--line);
          margin-left: 9px;
          padding-left: 18px;
          position: relative;
        }
        .pa-timeline-item:last-child { border-left: 2px solid transparent; }
        .pa-timeline-dot {
          position: absolute;
          left: -11px;
          top: 8px;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          border: 2px solid var(--line);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .pa-dot-positivo { border-color: var(--teal); }
        .pa-dot-negativo { border-color: var(--brick); }
        .pa-dot-neutral { border-color: #8A8371; }
        .pa-timeline-content {
          display: flex;
          align-items: baseline;
          gap: 10px;
          flex-wrap: wrap;
        }
        .pa-timeline-fecha {
          font-size: 12px;
          color: var(--ink-soft);
          min-width: 42px;
        }
        .pa-timeline-titulo {
          font-size: 14px;
          color: var(--ink);
        }
        .pa-timeline-toggle {
          margin: 10px 0 4px 0;
          padding: 0;
          background: none;
          border: none;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 13px;
          font-weight: 600;
          color: var(--ochre);
          cursor: pointer;
        }
        .pa-timeline-toggle:hover { text-decoration: underline; }

        .pa-timeline-expanded {
          max-width: 980px;
          margin: 14px auto 0 auto;
          padding: 0 24px;
        }
        .pa-timeline-nav {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 16px;
        }
        .pa-timeline-navbtn {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          border: 1px solid var(--line);
          background: white;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: var(--ink);
        }
        .pa-timeline-navbtn:disabled {
          opacity: 0.35;
          cursor: default;
        }
        .pa-timeline-month-label {
          font-family: 'Fraunces', serif;
          font-size: 16px;
          font-weight: 500;
          text-transform: capitalize;
          min-width: 130px;
        }
        .pa-timeline-close {
          margin-left: auto;
          color: var(--ink-soft);
        }

        .pa-timeline-summary {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1px;
          background: var(--line);
          border: 1px solid var(--line);
          margin-bottom: 6px;
        }
        .pa-summary-stat {
          background: white;
          padding: 14px 12px;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }
        .pa-summary-num {
          font-family: 'Fraunces', serif;
          font-size: 26px;
          font-weight: 600;
        }
        .pa-summary-lbl {
          font-size: 11.5px;
          color: var(--ink-soft);
          margin-top: 2px;
        }
        .pa-timeline-vacio {
          font-size: 13px;
          color: var(--ink-soft);
          padding: 12px 0;
        }
        .pa-summary-fuente {
          font-size: 11.5px;
          color: var(--ink-soft);
          margin: 0 0 18px 0;
        }
        .pa-summary-fuente a {
          color: var(--ochre);
          text-decoration: none;
        }
        .pa-summary-fuente a:hover { text-decoration: underline; }

        .pa-modal-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(18, 35, 43, 0.55);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          z-index: 50;
        }
        .pa-modal {
          background: white;
          width: 100%;
          max-width: 640px;
          padding: 22px 24px 26px 24px;
          border-radius: 4px;
        }
        .pa-modal-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 18px;
        }
        .pa-modal-label {
          font-size: 13px;
          color: var(--ink-soft);
        }
        .pa-modal-value {
          font-family: 'Fraunces', serif;
          font-size: 28px;
          font-weight: 500;
        }
        .pa-modal-close {
          background: none;
          border: none;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 13px;
          color: var(--ink-soft);
          cursor: pointer;
          padding: 4px 0;
        }
        .pa-modal-close:hover { color: var(--ink); }

        .pa-granularidad-row {
          display: flex;
          gap: 6px;
          margin-bottom: 14px;
        }
        .pa-granularidad-btn {
          padding: 5px 12px;
          border: 1px solid var(--line);
          border-radius: 14px;
          background: white;
          font-family: 'IBM Plex Sans', sans-serif;
          font-size: 12.5px;
          font-weight: 500;
          color: var(--ink-soft);
          cursor: pointer;
        }
        .pa-granularidad-btn.active {
          background: var(--dark);
          border-color: var(--dark);
          color: var(--paper);
        }
        .pa-noticias {
          max-width: 980px;
          margin: 14px auto 0 auto;
          padding: 0 24px 40px 24px;
        }
        .pa-noticia {
          padding: 20px 0;
          border-top: 1px solid var(--line);
        }
        .pa-noticia:first-child { border-top: none; padding-top: 8px; }
        .pa-noticia-kicker {
          font-size: 12px;
          color: var(--ochre);
          font-weight: 600;
        }
        .pa-noticia-fecha {
          font-size: 12px;
          color: var(--ink-soft);
        }
        .pa-noticia-titulo {
          font-family: 'Fraunces', serif;
          font-size: 22px;
          font-weight: 500;
          margin: 6px 0 6px 0;
          line-height: 1.25;
        }
        .pa-noticia-bajada {
          font-size: 14.5px;
          color: var(--ink-soft);
          line-height: 1.5;
          max-width: 640px;
        }

        .pa-footer {
          background: var(--dark);
          color: #A9BBC0;
          font-size: 12px;
          padding: 18px 24px;
          text-align: center;
        }
      `}</style>

      {/* MASTHEAD */}
      <div className="pa-masthead">
        <div className="pa-masthead-top">
          <div>
            <h1 className="pa-title pa-serif">Pulso Austral</h1>
            <div className="pa-tagline">El estado del país, medido.</div>
          </div>
          <div className="pa-date">
            {today}
            <span className={`pa-estado-conexion pa-estado-${estadoConexion}`}>
              {estadoConexion === "conectado" && "● datos en vivo"}
              {estadoConexion === "cargando" && "○ conectando…"}
              {(estadoConexion === "demo" || estadoConexion === "error") && "○ datos de ejemplo"}
            </span>
          </div>
        </div>

        {/* DOLARES — destacado arriba de todo */}
        <div className="pa-dollars">
          <div className="pa-dollar-block">
            <div className="pa-dollar-label">Dólar oficial</div>
            <div className="pa-dollar-value">${destacadosActivos.dolares.oficial.valor.toLocaleString("es-AR")}</div>
            <div className="pa-dollar-delta">
              <TrendIcon trend={destacadosActivos.dolares.oficial.delta > 0 ? "up" : "down"} />
              {Math.abs(destacadosActivos.dolares.oficial.delta)}% hoy
            </div>
          </div>
          <div className="pa-dollar-block">
            <div className="pa-dollar-label">Dólar blue</div>
            <div className="pa-dollar-value">${destacadosActivos.dolares.blue.valor.toLocaleString("es-AR")}</div>
            <div className="pa-dollar-delta">
              <TrendIcon trend={destacadosActivos.dolares.blue.delta > 0 ? "up" : "down"} />
              {Math.abs(destacadosActivos.dolares.blue.delta)}% hoy
            </div>
          </div>
          <div className="pa-dollar-block">
            <div className="pa-dollar-label">Merval</div>
            <div className="pa-dollar-value">{destacadosActivos.merval.valor.toLocaleString("es-AR")}</div>
            <div className="pa-dollar-delta">
              <TrendIcon trend={destacadosActivos.merval.delta > 0 ? "up" : "down"} />
              {Math.abs(destacadosActivos.merval.delta)}% hoy
            </div>
          </div>
          <div className="pa-brecha">
            <div className="pa-brecha-value">{brecha}%</div>
            <div className="pa-brecha-label">brecha cambiaria</div>
          </div>
        </div>

        {/* TICKER */}
        <div className="pa-ticker-wrap">
          <div className="pa-ticker">
            {[...TICKER, ...TICKER].map((item, i) => (
              <span className="pa-ticker-item" key={i}>
                {item.label} <b>{item.valor}</b> <TrendIcon trend={item.trend} size={12} />
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* NAV DE CATEGORIAS */}
      <div className="pa-nav">
        {categoriasActivas.map((c) => {
          const Icon = c.icon;
          return (
            <button
              key={c.id}
              className={`pa-nav-btn ${activeCat === c.id ? "active" : ""}`}
              onClick={() => setActiveCat(c.id)}
            >
              <Icon size={15} />
              {c.nombre}
            </button>
          );
        })}
      </div>

      {/* PANEL DE INDICADORES */}
      <div className="pa-panel">
        <div className="pa-grid">
          {cat.indicadores.map((ind, i) => (
            <div
              className={`pa-card ${ind.historias ? "pa-card-clickable" : ""}`}
              style={{ "--cat-color": cat.color }}
              key={i}
              onClick={ind.historias ? () => abrirIndicador(ind, cat.color) : undefined}
              role={ind.historias ? "button" : undefined}
              tabIndex={ind.historias ? 0 : undefined}
            >
              <div className="pa-card-label">{ind.label}</div>
              <div className="pa-card-value">{ind.valor}</div>
              <div className="pa-card-delta">
                <TrendIcon trend={ind.trend} size={12} />
                {ind.delta}
              </div>
              {ind.historias && (
                <div className="pa-card-spark">
                  <Sparkline data={ind.historias.meses.slice(-7).map((h) => h.valor)} color={cat.color} />
                </div>
              )}
              {ind.fuente && (
                <a
                  className="pa-card-fuente"
                  href={ind.fuente.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                >
                  ref: {ind.fuente.nombre}
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* LÍNEA DE TIEMPO */}
      <div className="pa-section-title">
        <Clock size={18} />
        Línea de tiempo
      </div>

      {!timelineExpandido ? (
        <div className="pa-timeline">
          {timelineReciente.map((ev, i) => (
            <div className="pa-timeline-item" key={i}>
              <div className={`pa-timeline-dot pa-dot-${ev.sentimiento}`}>
                <TrendIcon trend={sentimentTrend(ev.sentimiento)} size={11} />
              </div>
              <div className="pa-timeline-content">
                <span className="pa-timeline-fecha">{fechaCorta(ev.fecha)}</span>
                <span className="pa-timeline-titulo">{ev.titulo}</span>
              </div>
            </div>
          ))}
          <button className="pa-timeline-toggle" onClick={() => setTimelineExpandido(true)}>
            Ver línea de tiempo completa
          </button>
        </div>
      ) : (
        <div className="pa-timeline-expanded">
          <div className="pa-timeline-nav">
            <button
              className="pa-timeline-navbtn"
              onClick={() => setMesIdx((i) => Math.min(i + 1, mesesDisponibles.length - 1))}
              disabled={mesIdx >= mesesDisponibles.length - 1}
              aria-label="Mes anterior"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="pa-timeline-month-label">{mesActual?.label}</span>
            <button
              className="pa-timeline-navbtn"
              onClick={() => setMesIdx((i) => Math.max(i - 1, 0))}
              disabled={mesIdx <= 0}
              aria-label="Mes siguiente"
            >
              <ChevronRight size={16} />
            </button>
            <button className="pa-timeline-toggle pa-timeline-close" onClick={() => setTimelineExpandido(false)}>
              Cerrar línea de tiempo
            </button>
          </div>

          <div className="pa-timeline-summary">
            <div className="pa-summary-stat">
              <span className="pa-summary-num" style={{ color: "#1F6F6B" }}>{resumenMes.positivo}</span>
              <span className="pa-summary-lbl">Noticias positivas</span>
            </div>
            <div className="pa-summary-stat">
              <span className="pa-summary-num" style={{ color: "#A23B2E" }}>{resumenMes.negativo}</span>
              <span className="pa-summary-lbl">Noticias negativas</span>
            </div>
            <div className="pa-summary-stat">
              <span className="pa-summary-num" style={{ color: "#8A8371" }}>{resumenMes.neutral}</span>
              <span className="pa-summary-lbl">Noticias neutras</span>
            </div>
          </div>
          <div className="pa-summary-fuente">
            Clasificación propia en base a cobertura de medios nacionales —{" "}
            <a href="https://news.google.com/search?q=argentina%20econom%C3%ADa&hl=es-419&gl=AR&ceid=AR%3Aes-419" target="_blank" rel="noopener noreferrer">
              ver fuentes
            </a>
          </div>

          <div className="pa-timeline">
            {eventosDelMes.length === 0 && (
              <div className="pa-timeline-vacio">No hay eventos registrados este mes.</div>
            )}
            {eventosDelMes.map((ev, i) => (
              <div className="pa-timeline-item" key={i}>
                <div className={`pa-timeline-dot pa-dot-${ev.sentimiento}`}>
                  <TrendIcon trend={sentimentTrend(ev.sentimiento)} size={11} />
                </div>
                <div className="pa-timeline-content">
                  <span className="pa-timeline-fecha">{fechaCorta(ev.fecha)}</span>
                  <span className="pa-timeline-titulo">{ev.titulo}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* NOTICIAS */}
      <div className="pa-section-title">
        <Newspaper size={18} />
        Noticias de {cat.nombre}
      </div>
      <div className="pa-noticias">
        {noticiasFiltradas.map((n, i) => (
          <div className="pa-noticia" key={i}>
            <span className="pa-noticia-kicker">{n.kicker}</span>
            <span className="pa-noticia-fecha"> · {n.fecha}</span>
            <div className="pa-noticia-titulo">{n.titulo}</div>
            <div className="pa-noticia-bajada">{n.bajada}</div>
          </div>
        ))}
      </div>

      <div className="pa-footer">
        Fuentes: INDEC · BCRA · REM · Moody's / S&P — datos de ejemplo, a conectar con fuentes reales
      </div>

      {/* MODAL: GRÁFICO EXPANDIDO DE UN INDICADOR */}
      {indicadorExpandido && (
        <div className="pa-modal-backdrop" onClick={() => setIndicadorExpandido(null)}>
          <div className="pa-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pa-modal-header">
              <div>
                <div className="pa-modal-label">{indicadorExpandido.label}</div>
                <div className="pa-modal-value" style={{ color: indicadorExpandido.color }}>
                  {indicadorExpandido.valor}
                </div>
              </div>
              <button className="pa-modal-close" onClick={() => setIndicadorExpandido(null)}>
                Cerrar
              </button>
            </div>

            <div className="pa-granularidad-row">
              {GRANULARIDADES.map((g) => (
                <button
                  key={g.id}
                  className={`pa-granularidad-btn ${granularidad === g.id ? "active" : ""}`}
                  onClick={() => cambiarGranularidad(g.id)}
                >
                  {g.nombre}
                </button>
              ))}
            </div>

            <div className="pa-timeline-nav">
              <button
                className="pa-timeline-navbtn"
                onClick={() => setVentanaOffset((o) => Math.min(o + VENTANA, Math.max(0, indicadorExpandido.historias[granularidad].length - 1)))}
                disabled={ventanaOffset + VENTANA >= indicadorExpandido.historias[granularidad].length}
                aria-label="Período anterior"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="pa-timeline-month-label">{rangoLabel}</span>
              <button
                className="pa-timeline-navbtn"
                onClick={() => setVentanaOffset((o) => Math.max(o - VENTANA, 0))}
                disabled={ventanaOffset <= 0}
                aria-label="Período siguiente"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <ChartExpandido data={ventanaDatos} color={indicadorExpandido.color} />
          </div>
        </div>
      )}
    </div>
  );
}
