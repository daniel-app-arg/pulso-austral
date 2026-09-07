import { fetchCategorias, fetchIndicadores } from './api';
import type { CategoriaDTO, IndicadorDTO } from './types';

export interface GlosarioData {
  categorias: CategoriaDTO[];
  indicadores: IndicadorDTO[];
}

export async function getGlosario(): Promise<GlosarioData | null> {
  try {
    const [categorias, indicadores] = await Promise.all([fetchCategorias(), fetchIndicadores()]);
    return { categorias, indicadores };
  } catch (err) {
    console.warn('No se pudo traer el glosario de indicadores:', err);
    return null;
  }
}
