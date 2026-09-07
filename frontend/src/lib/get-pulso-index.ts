import { fetchPulsoIndex } from './api';
import type { PulsoIndexDTO } from './types';

/** A diferencia del dashboard principal, si el backend no responde no se
 * inventa un score — no tendría sentido mostrar un número de "cómo va el
 * país" que en realidad no se calculó. Se oculta el banner (null) en vez
 * de mostrar un dato ficticio. */
export async function getPulsoIndex(): Promise<PulsoIndexDTO | null> {
  try {
    return await fetchPulsoIndex();
  } catch (err) {
    console.warn('No se pudo traer el índice general:', err);
    return null;
  }
}
