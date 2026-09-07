import { Footer } from '@/components/Footer';
import { GobiernosComparativa } from '@/components/GobiernosComparativa';
import { PageHeader } from '@/components/PageHeader';
import { getGobiernosComparativa } from '@/lib/get-gobiernos-comparativa';

export const dynamic = 'force-dynamic';

export default async function GobiernosPage() {
  const data = await getGobiernosComparativa();

  return (
    <div>
      <PageHeader />

      <p className="pa-page-intro">
        Todos los indicadores del dashboard, resumidos para cada mandato presidencial
        de 4 años: el valor al inicio, al final (o a hoy, si el mandato sigue en
        curso) y la variación entre ambos. Los mandatos anteriores a la ventana de
        datos reales que carga este sitio pueden aparecer sin datos en varios
        indicadores — no significa que no existan, sino que todavía no se cargó esa
        serie histórica.
      </p>

      {data === null && (
        <p className="pa-page-intro">No se pudo conectar con el backend para traer la comparativa por gobierno.</p>
      )}

      {data && <GobiernosComparativa categorias={data.categorias} resumenes={data.resumenes} />}

      <Footer />
    </div>
  );
}
