import { fetchMedios } from './api';
import type { MedioDTO } from './types';

export async function getMedios(): Promise<MedioDTO[] | null> {
  try {
    return await fetchMedios();
  } catch (err) {
    console.warn('No se pudo traer el directorio de medios:', err);
    return null;
  }
}
