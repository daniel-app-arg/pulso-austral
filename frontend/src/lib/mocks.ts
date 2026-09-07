import { MESES } from './format';
import type { CategoriaVM, DashboardData, EventoTimelineVM, Historias, IndicadorVM, NoticiaVM, PuntoSerie, Trend } from './types';

// ---------------------------------------------------------------------------
// Datos de respaldo — puerto directo del mock de pulso-austral.jsx. Se usan
// solo si el backend Django no responde, para que el dashboard nunca se
// rompa por falta de conexión (mismo principio que tenía el artifact
// original con Supabase).
// ---------------------------------------------------------------------------

function periodosHastaHoy(n: number): string[] {
  const base = new Date(2026, 8, 1);
  const out: string[] = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(base.getFullYear(), base.getMonth() - i, 1);
    out.push(`${MESES[d.getMonth()].slice(0, 3)}-${String(d.getFullYear()).slice(2)}`);
  }
  return out;
}
const PERIODOS_14M = periodosHastaHoy(14);

function anios(n: number): string[] {
  const out: string[] = [];
  for (let i = n - 1; i >= 0; i--) out.push(String(2026 - i));
  return out;
}
const ANIOS_10 = anios(10);

function serieMensual(valores: number[]): PuntoSerie[] {
  return PERIODOS_14M.map((label, i) => ({ label, valor: valores[i] }));
}
function serieAnual(valores: number[]): PuntoSerie[] {
  return ANIOS_10.map((label, i) => ({ label, valor: valores[i] }));
}

function historias(mensuales: number[], anuales: number[]): Historias {
  return { meses: serieMensual(mensuales), anios: serieAnual(anuales) };
}

interface IndicadorMock {
  label: string;
  valor: string;
  delta: string;
  trend: Trend;
  fuente?: { nombre: string; url: string };
  historias?: Historias | null;
}

const MOCK_CATEGORIAS: { id: string; nombre: string; icono: string; color: string; indicadores: IndicadorMock[] }[] = [
  {
    id: 'macro',
    nombre: 'Macroeconomía',
    icono: 'Landmark',
    color: '#C98A2C',
    indicadores: [
      {
        label: 'Inflación interanual', valor: '118%', delta: '-42pp vs. año anterior', trend: 'down',
        fuente: { nombre: 'INDEC', url: 'https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31' },
        historias: historias(
          [268, 245, 225, 205, 188, 172, 158, 146, 136, 128, 122, 120, 119, 118],
          [25, 48, 54, 36, 51, 95, 140, 190, 230, 118],
        ),
      },
      {
        label: 'Riesgo país (EMBI)', valor: '612 pb', delta: '-38pb en el mes', trend: 'down',
        fuente: { nombre: 'Ámbito Financiero', url: 'https://www.ambito.com/contenidos/riesgo-pais.html' },
        historias: historias(
          [950, 910, 880, 850, 820, 790, 760, 730, 700, 670, 650, 635, 620, 612],
          [450, 550, 800, 1500, 1700, 2000, 1900, 1600, 900, 612],
        ),
      },
      {
        label: 'Reservas netas BCRA', valor: 'US$ 29.400 M', delta: '+US$1.200M en el mes', trend: 'up',
        fuente: { nombre: 'BCRA', url: 'https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp' },
        historias: historias(
          [18.0, 18.5, 19.2, 20.0, 20.8, 21.5, 22.3, 23.1, 24.0, 24.9, 25.8, 27.0, 28.2, 29.4],
          [10, 8, 5, 3, -3, -5, 2, 10, 18, 29.4],
        ),
      },
      {
        label: 'Resultado fiscal primario', valor: '+0.3% PBI', delta: 'superávit 8vo mes', trend: 'up',
        fuente: { nombre: 'Ministerio de Economía', url: 'https://www.argentina.gob.ar/economia' },
        historias: historias(
          [-1.8, -1.5, -1.3, -1.0, -0.8, -0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.15, 0.25, 0.3],
          [-4.2, -3.8, -3.5, -6.5, -3.0, -2.4, -1.5, -0.5, -0.2, 0.3],
        ),
      },
    ],
  },
  {
    id: 'empleo',
    nombre: 'Empleo y trabajo',
    icono: 'Users',
    color: '#1F6F6B',
    indicadores: [
      {
        label: 'Desempleo', valor: '7.2%', delta: '+0.3pp vs. trim. anterior', trend: 'up',
        fuente: { nombre: 'INDEC', url: 'https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58' },
        historias: historias(
          [6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, 7.0, 7.1, 7.2],
          [8.3, 9.1, 9.8, 11.5, 8.7, 7.1, 6.2, 6.9, 7.5, 7.2],
        ),
      },
      {
        label: 'Salario real', valor: '-1.4%', delta: 'interanual', trend: 'down',
        fuente: { nombre: 'INDEC', url: 'https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31' },
        historias: historias(
          [-6.5, -6.0, -5.5, -5.0, -4.5, -4.0, -3.5, -3.0, -2.6, -2.2, -1.9, -1.7, -1.6, -1.4],
          [3.0, -2.0, -5.7, -2.5, 4.0, -3.0, -12.0, -8.0, -4.0, -1.4],
        ),
      },
      {
        label: 'Empleo informal', valor: '41.8%', delta: 'sin cambios', trend: 'flat',
        fuente: { nombre: 'INDEC', url: 'https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58' },
        historias: historias(
          [42.5, 42.3, 42.1, 42.0, 41.9, 42.0, 41.9, 41.8, 41.9, 41.8, 41.9, 41.8, 41.9, 41.8],
          [33.5, 34.0, 35.1, 36.8, 36.0, 35.5, 38.0, 40.5, 42.0, 41.8],
        ),
      },
      {
        label: 'Canasta básica total', valor: '$1.150.000', delta: 'familia tipo, +2.1% mensual', trend: 'up',
        fuente: { nombre: 'INDEC', url: 'https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-46-153' },
        historias: historias(
          [850000, 880000, 910000, 940000, 970000, 1000000, 1030000, 1060000, 1080000, 1100000, 1115000, 1130000, 1140000, 1150000],
          [18000, 25000, 38000, 55000, 95000, 190000, 420000, 750000, 980000, 1150000],
        ),
      },
    ],
  },
  {
    id: 'geo',
    nombre: 'Geopolítica',
    icono: 'Globe2',
    color: '#A23B2E',
    indicadores: [
      { label: 'Acuerdo con el FMI', valor: 'En revisión', delta: 'próximo desembolso: oct.', trend: 'flat', historias: null, fuente: { nombre: 'FMI', url: 'https://www.imf.org/en/Countries/ARG' } },
      { label: 'Calificación soberana', valor: 'CCC+', delta: 'perspectiva positiva (S&P)', trend: 'up', historias: null, fuente: { nombre: 'S&P Global Ratings', url: 'https://www.spglobal.com/ratings/en/' } },
      { label: 'Swap con China', valor: 'US$ 5.000 M activos', delta: 'sin cambios en el trimestre', trend: 'flat', historias: null, fuente: { nombre: 'BCRA', url: 'https://www.bcra.gob.ar/' } },
      { label: 'Mercosur–UE', valor: 'Acuerdo firmado', delta: 'pendiente ratificación', trend: 'up', historias: null, fuente: { nombre: 'Mercosur', url: 'https://www.mercosur.int/' } },
    ],
  },
];

const MOCK_TIMELINE: EventoTimelineVM[] = [
  { fecha: '2026-09-07', titulo: 'Brecha cambiaria en su mínimo de 8 meses', sentimiento: 'positivo', categoria: 'macro' },
  { fecha: '2026-09-06', titulo: 'Salario real mejora por primera vez en el año', sentimiento: 'positivo', categoria: 'empleo' },
  { fecha: '2026-09-06', titulo: 'Misión del FMI llega para revisar metas fiscales', sentimiento: 'neutral', categoria: 'geo' },
  { fecha: '2026-09-04', titulo: 'BCRA acumula reservas por cuarta semana consecutiva', sentimiento: 'positivo', categoria: 'macro' },
  { fecha: '2026-09-03', titulo: 'Avanza la ratificación del acuerdo Mercosur–UE', sentimiento: 'positivo', categoria: 'geo' },
  { fecha: '2026-09-02', titulo: 'Sube el empleo registrado en la construcción', sentimiento: 'positivo', categoria: 'empleo' },
  { fecha: '2026-08-29', titulo: 'Suba en la tasa de desempleo del segundo trimestre', sentimiento: 'negativo', categoria: 'empleo' },
  { fecha: '2026-08-27', titulo: 'S&P sube la perspectiva de la calificación soberana', sentimiento: 'positivo', categoria: 'geo' },
  { fecha: '2026-08-22', titulo: 'El dólar blue subió tres ruedas seguidas', sentimiento: 'negativo', categoria: 'macro' },
  { fecha: '2026-08-18', titulo: 'Cae la producción industrial por segundo mes', sentimiento: 'negativo', categoria: 'macro' },
  { fecha: '2026-08-14', titulo: 'Tensión comercial por trabas para importar insumos', sentimiento: 'negativo', categoria: 'geo' },
  { fecha: '2026-08-09', titulo: 'Se recupera el poder de compra del salario mínimo', sentimiento: 'positivo', categoria: 'empleo' },
  { fecha: '2026-08-05', titulo: 'El Merval marcó un nuevo máximo en pesos', sentimiento: 'positivo', categoria: 'macro' },
  { fecha: '2026-07-30', titulo: 'El Gobierno cerró el acuerdo técnico con el FMI', sentimiento: 'positivo', categoria: 'geo' },
  { fecha: '2026-07-24', titulo: 'Aumentó la informalidad laboral en el segundo trimestre', sentimiento: 'negativo', categoria: 'empleo' },
  { fecha: '2026-07-19', titulo: "Moody's mantuvo la calificación soberana sin cambios", sentimiento: 'neutral', categoria: 'geo' },
  { fecha: '2026-07-11', titulo: 'La inflación núcleo volvió a acelerarse', sentimiento: 'negativo', categoria: 'macro' },
  { fecha: '2026-07-03', titulo: 'Se creó empleo privado por primera vez en el año', sentimiento: 'positivo', categoria: 'empleo' },
];

const MOCK_NOTICIAS: NoticiaVM[] = [
  { categoria: 'macro', kicker: 'Economía', fecha: '7 de septiembre', titulo: 'La brecha cambiaria se achica por tercera semana consecutiva', bajada: 'El spread entre el dólar oficial y el blue cayó a su nivel más bajo en ocho meses, impulsado por la mayor oferta de divisas del agro.', url: '', medio: '' },
  { categoria: 'macro', kicker: 'Economía', fecha: '4 de septiembre', titulo: 'El Banco Central acumuló reservas por cuarta semana al hilo', bajada: 'Las compras se explican por la liquidación del agro y una mayor demanda de pesos estacional.', url: '', medio: '' },
  { categoria: 'empleo', kicker: 'Trabajo', fecha: '6 de septiembre', titulo: 'El salario real mostró la primera mejora mensual del año', bajada: 'Paritarias por encima de la inflación en tres sectores clave frenaron, por ahora, la caída del poder adquisitivo.', url: '', medio: '' },
  { categoria: 'empleo', kicker: 'Trabajo', fecha: '2 de septiembre', titulo: 'Crece el empleo registrado en la construcción', bajada: 'Es el tercer mes de recuperación tras la fuerte caída del año pasado, según datos del Ministerio de Trabajo.', url: '', medio: '' },
  { categoria: 'geo', kicker: 'Geopolítica', fecha: '6 de septiembre', titulo: 'El Gobierno negocia un nuevo tramo de desembolsos con el FMI', bajada: 'La misión del organismo llega a Buenos Aires la semana próxima para revisar el cumplimiento de las metas fiscales del segundo semestre.', url: '', medio: '' },
  { categoria: 'geo', kicker: 'Geopolítica', fecha: '3 de septiembre', titulo: 'Avanza la ratificación del acuerdo Mercosur–Unión Europea', bajada: 'Cancillería espera que el tratado esté listo para su firma definitiva antes de fin de año.', url: '', medio: '' },
];

function toIndicadorVM(id: string, m: IndicadorMock): IndicadorVM {
  return {
    id,
    label: m.label,
    valor: m.valor,
    delta: m.delta,
    trend: m.trend,
    fuente: m.fuente ?? null,
    historias: m.historias ?? null,
  };
}

export function datosMock(): DashboardData {
  const categorias: CategoriaVM[] = MOCK_CATEGORIAS.map((c) => ({
    id: c.id,
    nombre: c.nombre,
    color: c.color,
    icono: c.icono,
    indicadores: c.indicadores.map((ind, i) => toIndicadorVM(`${c.id}_${i}`, ind)),
  }));

  return {
    categorias,
    timeline: MOCK_TIMELINE,
    noticias: MOCK_NOTICIAS,
    destacados: {
      dolares: { oficial: { valor: 1042, delta: 0.4 }, blue: { valor: 1380, delta: -0.7 } },
      merval: { valor: 1852340, delta: 1.8 },
      brecha: 32,
    },
    ticker: [
      { label: 'Inflación mensual', valor: '3.1%', trend: 'down' },
      { label: 'Riesgo país', valor: '612 pb', trend: 'down' },
      { label: 'Merval', valor: '+1.8%', trend: 'up' },
      { label: 'Reservas BCRA', valor: 'US$ 29.400 M', trend: 'up' },
      { label: 'EMAE', valor: '+0.6%', trend: 'up' },
      { label: 'Desempleo', valor: '7.2%', trend: 'flat' },
    ],
    fuenteDatos: 'mock',
  };
}
