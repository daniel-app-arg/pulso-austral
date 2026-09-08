import type { DatosCrudos } from './api';
import { etiquetaDesdeFecha, fechaLarga, formatearNumero } from './format';
import type {
  CategoriaVM,
  DashboardData,
  DestacadosVM,
  EventoTimelineVM,
  Historias,
  IndicadorValorDTO,
  IndicadorVM,
  NoticiaVM,
  PuntoSerie,
} from './types';

// ---------------------------------------------------------------------------
// De las filas planas que devuelve la API Django a los modelos de vista que
// consume la UI — puerto directo de construirCategoriasDesdeDB /
// construirIndicadorDesdeDB / construirTimelineDesdeDB /
// construirNoticiasDesdeDB / construirDestacadosDesdeDB en pulso-austral.jsx.
// ---------------------------------------------------------------------------

const GRAN_A_CLAVE: Record<string, keyof Historias> = {
  dia: 'dias',
  semana: 'semanas',
  mes: 'meses',
  anio: 'anios',
};

function numero(v: string | null): number | null {
  if (v === null || v === '') return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

function construirIndicador(ind: DatosCrudos['indicadores'][number], valores: IndicadorValorDTO[]): IndicadorVM {
  const propios = valores.filter((v) => v.indicador_id === ind.id);
  const porGranularidad: Historias = {};

  propios.forEach((v) => {
    const clave = GRAN_A_CLAVE[v.granularidad];
    if (!clave) return;
    const punto: PuntoSerie = {
      label: etiquetaDesdeFecha(v.fecha, v.granularidad),
      valor: ind.tipo === 'cualitativo' ? v.valor_texto : numero(v.valor_numerico) ?? v.valor_texto,
      delta: v.delta_texto,
      trend: (v.trend || undefined) as PuntoSerie['trend'],
    };
    (porGranularidad[clave] ??= []).push(punto);
  });

  // Última entrada disponible, con preferencia mes > año > semana > día para
  // el valor "actual" que pinta la tarjeta (coincide con el orden en que se
  // cargan las series ilustrativas del seed).
  const ultimo =
    porGranularidad.meses?.at(-1) ??
    porGranularidad.anios?.at(-1) ??
    porGranularidad.semanas?.at(-1) ??
    porGranularidad.dias?.at(-1);

  const tieneHistoria = Object.values(porGranularidad).some((serie) => (serie?.length ?? 0) > 1);

  const valorFormateado =
    typeof ultimo?.valor === 'number' ? formatearNumero(ultimo.valor) : (ultimo?.valor ?? '—');

  return {
    id: ind.id,
    label: ind.nombre,
    valor: ind.tipo === 'cualitativo' ? String(valorFormateado) : `${valorFormateado}${ind.unidad ? ' ' + ind.unidad : ''}`,
    delta: ultimo?.delta || '',
    trend: (ultimo?.trend as IndicadorVM['trend']) || 'flat',
    polaridad: ind.polaridad,
    fuente: ind.fuente ? { nombre: ind.fuente.nombre, url: ind.fuente.url } : null,
    historias: ind.tipo === 'numerico' && tieneHistoria ? porGranularidad : null,
  };
}

export function construirCategorias({ categorias, indicadores, valores }: DatosCrudos): CategoriaVM[] {
  return categorias
    .slice()
    .sort((a, b) => a.orden - b.orden)
    .map((c) => ({
      id: c.id,
      nombre: c.nombre,
      color: c.color,
      icono: c.icono,
      indicadores: indicadores
        .filter((i) => i.categoria_id === c.id)
        .sort((a, b) => a.orden - b.orden)
        .map((i) => construirIndicador(i, valores)),
    }));
}

export function construirTimeline({ eventos }: DatosCrudos): EventoTimelineVM[] {
  return eventos.map((e) => ({ fecha: e.fecha, titulo: e.titulo, sentimiento: e.sentimiento, categoria: e.categoria_id }));
}

export function construirNoticias({ noticias }: DatosCrudos): NoticiaVM[] {
  return noticias.map((n) => ({
    categoria: n.categoria_id,
    kicker: n.kicker,
    fecha: fechaLarga(n.fecha),
    titulo: n.titulo,
    bajada: n.bajada,
    url: n.url,
    medio: n.medio?.nombre ?? '',
  }));
}

export function construirDestacados({ destacados }: DatosCrudos): DestacadosVM {
  return {
    dolares: {
      oficial: {
        valor: destacados.dolares.oficial?.valor ?? 0,
        delta: destacados.dolares.oficial?.delta ?? 0,
      },
      blue: {
        valor: destacados.dolares.blue?.valor ?? 0,
        delta: destacados.dolares.blue?.delta ?? 0,
      },
    },
    merval: destacados.merval ? { valor: destacados.merval.valor, delta: destacados.merval.delta } : null,
    brecha: destacados.brecha ?? 0,
  };
}

// El ticker de la cinta superior no tiene tabla propia: se arma a partir de
// un puñado de indicadores elegidos a mano, igual de espíritu a como el
// artifact original tenía el array TICKER escrito a mano.
const TICKER_IDS = ['inflacion_interanual', 'riesgo_pais', 'merval', 'reservas_bcra', 'emae', 'desempleo'];

export function construirTicker(categorias: CategoriaVM[]): DashboardData['ticker'] {
  const porId = new Map(categorias.flatMap((c) => c.indicadores).map((i) => [i.id, i]));
  return TICKER_IDS.map((id) => porId.get(id))
    .filter((ind): ind is NonNullable<typeof ind> => Boolean(ind))
    .map((ind) => ({ label: ind.label, valor: ind.valor, trend: ind.trend, polaridad: ind.polaridad }));
}

export function construirDashboardData(crudos: DatosCrudos): DashboardData {
  const categorias = construirCategorias(crudos);
  return {
    categorias,
    timeline: construirTimeline(crudos),
    noticias: construirNoticias(crudos),
    destacados: construirDestacados(crudos),
    ticker: construirTicker(categorias),
    fuenteDatos: 'api',
  };
}
