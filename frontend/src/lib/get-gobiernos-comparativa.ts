import { fetchCategorias, fetchGobiernoResumen, fetchGobiernos } from './api';
import type { CategoriaDTO, GobiernoResumenDTO } from './types';

export interface GobiernosComparativaData {
  categorias: CategoriaDTO[];
  resumenes: GobiernoResumenDTO[];
}

/** Trae la lista de gobiernos, categorías (para agrupar/rotular), y el
 * resumen de cada gobierno — todo de una sola vez, server-side, para que la
 * comparativa en el cliente sea instantánea al cambiar de gobierno (sin
 * fetches nuevos por cada clic). Son pocos gobiernos y el payload de cada
 * resumen es chico, así que traer los 6 de antemano es barato. */
export async function getGobiernosComparativa(): Promise<GobiernosComparativaData | null> {
  try {
    const [categorias, gobiernos] = await Promise.all([fetchCategorias(), fetchGobiernos()]);
    const resumenes = await Promise.all(gobiernos.map((g) => fetchGobiernoResumen(g.id)));
    return { categorias, resumenes };
  } catch (err) {
    console.warn('No se pudo traer la comparativa por gobierno:', err);
    return null;
  }
}
