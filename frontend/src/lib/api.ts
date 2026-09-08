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

// Los datos no cambian en tiempo real: se actualizan cuando corre
// `fetch_datos_reales` (indicadores automáticos) o cuando se corre un
// seed manual (histórico, esporádico) — así que cachear la respuesta de
// la API no le resta nada de "actualidad" al sitio, pero evita volver a
// pegarle a Django/Neon en cada visita. Antes esto era `cache:
// 'no-store'` en todos los fetches (sin excepción), lo que apagaba por
// completo el cache de Next.js: cada carga de página, de cada
// visitante, disparaba un round-trip nuevo — incluidas las 2 páginas
// secuenciales de indicador-valores y el cálculo completo de
// GobiernoResumenView sobre ~50 indicadores. Con el sitio corriendo en
// planes gratis (Render se "duerme" a los 15 min sin uso, Neon
// suspende su cómputo), eso hacía que la carga tardara 8-19s SIEMPRE,
// no solo en el primer visitante tras la inactividad.
//
// De todos los indicadores, el único que efectivamente se actualiza
// varias veces por día es `/destacados/` (dólar oficial, dólar blue y
// Merval — 2 veces por día). Todo lo demás (el resto de los
// indicadores, noticias, línea de tiempo, gobiernos) cambia mucho más
// esporádicamente. Originalmente esto se cacheaba una semana entera,
// pero el cache de fetch de Next.js en Vercel persiste ENTRE deploys
// (no se limpia solo por subir código nuevo) — así que una carga
// manual de datos (correr un seed) podía tardar hasta una semana en
// verse en producción, sin forma de forzarlo desde acá sin acceso al
// dashboard de Vercel. Se baja a 1 día como mejor punto medio: sigue
// evitando pegarle a Django/Neon en cada visita, pero una actualización
// de datos tarda como mucho un día en reflejarse sola.
const REVALIDATE_DESTACADOS = 60 * 60 * 3; // 3 h — dólar/Merval, únicos que se actualizan 2x/día
const REVALIDATE_LARGO = 60 * 60 * 24; // 1 día — todo lo demás

interface Paginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function apiGet<T>(path: string, revalidate: number = REVALIDATE_LARGO): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { next: { revalidate } });
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
async function apiGetAll<T>(path: string, revalidate: number = REVALIDATE_LARGO): Promise<T[]> {
  const sep = path.includes('?') ? '&' : '?';
  let url: string | null = `${API_BASE_URL}${path}${sep}limit=2000`;
  const salida: T[] = [];
  for (let pagina = 0; url && pagina < 20; pagina++) {
    const res = await fetch(url, { next: { revalidate } });
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
    apiGet<DestacadosDTO>('/destacados/', REVALIDATE_DESTACADOS),
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
