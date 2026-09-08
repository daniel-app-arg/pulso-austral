import type {
  CategoriaDTO,
  DestacadosDTO,
  EventoTimelineDTO,
  GobiernoDTO,
  GobiernoResumenDTO,
  IndicadorDTO,
  IndicadorValorDTO,
  MedioDTO,
  NoticiaDTO,
  PulsoIndexDTO,
} from './types';

// ---------------------------------------------------------------------------
// Cliente del backend Django — reemplaza a la vieja capa `supaFetch` del
// artifact (fetch nativo a la REST API de Supabase). Corre en el servidor
// (Server Components de Next.js), así que no hay problema de CORS acá; solo
// aplicaría si en el futuro se agrega algún fetch desde un Client Component.
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000/api';

interface Paginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`API respondió ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

/** Trae una colección paginada completa, siguiendo `next` hasta agotarla —
 * las series diarias (BCRA) crecen solas con el tiempo, así que un límite
 * fijo de una sola página eventualmente se queda corto y trunca datos en
 * silencio (pasó con indicador-valores al pasar de ~1.800 a ~2.200 filas).
 * Tope de 20 páginas (40.000 filas) como salvaguarda ante un `next` que no
 * termine de agotarse nunca. */
async function apiGetAll<T>(path: string): Promise<T[]> {
  const sep = path.includes('?') ? '&' : '?';
  let url: string | null = `${API_BASE_URL}${path}${sep}limit=2000`;
  const salida: T[] = [];
  for (let pagina = 0; url && pagina < 20; pagina++) {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) {
      throw new Error(`API respondió ${res.status} en ${path}`);
    }
    const data: Paginada<T> = await res.json();
    salida.push(...data.results);
    url = data.next;
  }
  return salida;
}

export interface DatosCrudos {
  categorias: CategoriaDTO[];
  indicadores: IndicadorDTO[];
  valores: IndicadorValorDTO[];
  eventos: EventoTimelineDTO[];
  noticias: NoticiaDTO[];
  destacados: DestacadosDTO;
}

export async function fetchDatosCrudos(): Promise<DatosCrudos> {
  const [categorias, indicadores, valores, eventos, noticias, destacados] = await Promise.all([
    apiGetAll<CategoriaDTO>('/categorias/'),
    apiGetAll<IndicadorDTO>('/indicadores/'),
    apiGetAll<IndicadorValorDTO>('/indicador-valores/'),
    apiGetAll<EventoTimelineDTO>('/eventos-timeline/'),
    apiGetAll<NoticiaDTO>('/noticias/'),
    apiGet<DestacadosDTO>('/destacados/'),
  ]);
  return { categorias, indicadores, valores, eventos, noticias, destacados };
}

export async function fetchCategorias(): Promise<CategoriaDTO[]> {
  return apiGetAll<CategoriaDTO>('/categorias/');
}

export async function fetchIndicadores(): Promise<IndicadorDTO[]> {
  return apiGetAll<IndicadorDTO>('/indicadores/');
}

export async function fetchMedios(): Promise<MedioDTO[]> {
  return apiGetAll<MedioDTO>('/medios/');
}

export async function fetchGobiernos(): Promise<GobiernoDTO[]> {
  return apiGetAll<GobiernoDTO>('/gobiernos/');
}

export async function fetchPulsoIndex(): Promise<PulsoIndexDTO> {
  return apiGet<PulsoIndexDTO>('/pulso-index/');
}

export async function fetchGobiernoResumen(id: string): Promise<GobiernoResumenDTO> {
  return apiGet<GobiernoResumenDTO>(`/gobiernos/${id}/resumen/`);
}
