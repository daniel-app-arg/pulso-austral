// ---------------------------------------------------------------------------
// DTOs: la forma exacta en que responde la API de Django (ver
// backend/indicadores/serializers.py). Los nombres (categoria_id,
// indicador_id, fuente anidada) están calcados a propósito de la vieja capa
// supaFetch del artifact original.
// ---------------------------------------------------------------------------

export interface FuenteDTO {
  id: number;
  nombre: string;
  url: string;
}

export interface CategoriaDTO {
  id: string;
  nombre: string;
  color: string;
  icono: string;
  orden: number;
}

export type TipoIndicador = 'numerico' | 'cualitativo';
export type Granularidad = 'dia' | 'semana' | 'mes' | 'anio';
export type Trend = 'up' | 'down' | 'flat';
export type Sentimiento = 'positivo' | 'negativo' | 'neutral';

export interface IndicadorDTO {
  id: string;
  categoria_id: string;
  nombre: string;
  tipo: TipoIndicador;
  unidad: string;
  destacado: boolean;
  actualizacion_automatica: boolean;
  polaridad: 'positivo' | 'negativo' | 'neutral';
  metodologia: string;
  fuente: FuenteDTO | null;
  orden: number;
}

export interface IndicadorValorDTO {
  id: number;
  indicador_id: string;
  fecha: string; // ISO yyyy-mm-dd
  granularidad: Granularidad;
  valor_numerico: string | null; // DRF serializa Decimal como string
  valor_texto: string;
  delta_texto: string;
  trend: Trend | '';
}

export interface EventoTimelineDTO {
  id: number;
  fecha: string;
  titulo: string;
  categoria_id: string;
  sentimiento: Sentimiento;
  fuente: FuenteDTO | null;
}

export interface NoticiaDTO {
  id: number;
  categoria_id: string;
  kicker: string;
  fecha: string;
  titulo: string;
  bajada: string;
  cuerpo: string;
  url: string;
  medio: MedioDTO | null;
  publicado: boolean;
}

export interface DestacadoValorDTO {
  valor: number;
  delta: number;
  fecha: string;
}

export interface DestacadosDTO {
  dolares: {
    oficial: DestacadoValorDTO | null;
    blue: DestacadoValorDTO | null;
  };
  merval: DestacadoValorDTO | null;
  brecha: number | null;
}

export type OrientacionPolitica = 'izquierda' | 'centro_izquierda' | 'centro' | 'centro_derecha' | 'derecha';
export type TipoMedio = 'diario' | 'agencia' | 'tv' | 'radio' | 'revista' | 'factchecking';

export interface MedioDTO {
  id: string;
  nombre: string;
  url: string;
  tipo: TipoMedio;
  orientacion: OrientacionPolitica;
  descripcion: string;
  orden: number;
}

export type DireccionIndicador = 'mejora' | 'empeora' | 'sin_cambio';

export interface PulsoIndexDetalleDTO {
  id: string;
  nombre: string;
  categoria_id: string;
  polaridad: 'positivo' | 'negativo';
  trend: Trend;
  direccion: DireccionIndicador;
  fecha: string;
}

export interface PulsoIndexDTO {
  score: number;
  fecha: string;
  trend: Trend | null;
  delta: number | null;
  mejorando: number;
  empeorando: number;
  sin_cambio: number;
  total: number;
  historial: { fecha: string; score: number }[];
  detalle: PulsoIndexDetalleDTO[];
}

export interface GobiernoDTO {
  id: string;
  presidente: string;
  partido: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  color: string;
  orden: number;
}

export interface ResumenIndicadorDTO {
  id: string;
  nombre: string;
  categoria_id: string;
  tipo: TipoIndicador;
  unidad: string;
  fuente: FuenteDTO | null;
  sin_datos: boolean;
  valor_inicio?: number | string | null;
  valor_fin?: number | string | null;
  variacion_abs?: number | null;
  variacion_pct?: number | null;
  promedio?: number | null;
  fecha_inicio?: string;
  fecha_fin?: string;
  cantidad_puntos?: number;
}

export interface GobiernoResumenDTO {
  gobierno: GobiernoDTO;
  desde: string;
  hasta: string;
  indicadores: ResumenIndicadorDTO[];
}

// ---------------------------------------------------------------------------
// Modelos de vista: la forma que consume la UI, igual a la que ya usaban los
// mocks del artifact original (CATEGORIAS/TIMELINE/NOTICIAS).
// ---------------------------------------------------------------------------

export interface Fuente {
  nombre: string;
  url: string;
}

export interface PuntoSerie {
  label: string;
  valor: number | string;
  delta?: string;
  trend?: Trend;
}

export type Historias = Partial<Record<'dias' | 'semanas' | 'meses' | 'anios', PuntoSerie[]>>;

export interface IndicadorVM {
  id: string;
  label: string;
  valor: string;
  delta: string;
  trend: Trend;
  fuente: Fuente | null;
  historias: Historias | null;
}

export interface CategoriaVM {
  id: string;
  nombre: string;
  color: string;
  icono: string;
  indicadores: IndicadorVM[];
}

export interface EventoTimelineVM {
  fecha: string;
  titulo: string;
  sentimiento: Sentimiento;
  categoria: string;
}

export interface NoticiaVM {
  categoria: string;
  kicker: string;
  fecha: string; // ya formateada, "7 de septiembre"
  titulo: string;
  bajada: string;
  url: string; // puede quedar roto con el tiempo — titulo/bajada no dependen de esto
  medio: string; // nombre del medio, '' si no se cargó
}

export interface DestacadosVM {
  dolares: {
    oficial: { valor: number; delta: number };
    blue: { valor: number; delta: number };
  };
  merval: { valor: number; delta: number };
  brecha: number;
}

export interface DashboardData {
  categorias: CategoriaVM[];
  timeline: EventoTimelineVM[];
  noticias: NoticiaVM[];
  destacados: DestacadosVM;
  ticker: { label: string; valor: string; trend: Trend }[];
  fuenteDatos: 'api' | 'mock';
}
