import { fetchDatosCrudos } from './api';
import { datosMock } from './mocks';
import { construirDashboardData } from './transform';
import type { DashboardData } from './types';

/** Trae los datos del backend Django; si no responde, cae a los mocks para
 * que el dashboard nunca se rompa por falta de conexión. */
export async function getDashboardData(): Promise<DashboardData> {
  try {
    const crudos = await fetchDatosCrudos();
    return construirDashboardData(crudos);
  } catch (err) {
    console.warn('No se pudo conectar a la API de Pulso Austral, usando datos de ejemplo:', err);
    return datosMock();
  }
}
