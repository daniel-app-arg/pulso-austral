import { Dashboard } from '@/components/Dashboard';
import { getDashboardData } from '@/lib/get-dashboard-data';
import { getPulsoIndex } from '@/lib/get-pulso-index';

// El dashboard siempre debe reflejar el último dato cargado en el backend —
// nunca se sirve una versión vieja cacheada.
export const dynamic = 'force-dynamic';

export default async function Page() {
  const [data, pulsoIndex] = await Promise.all([getDashboardData(), getPulsoIndex()]);
  return <Dashboard data={data} pulsoIndex={pulsoIndex} />;
}
