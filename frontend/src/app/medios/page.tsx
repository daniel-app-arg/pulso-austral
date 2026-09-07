import { Footer } from '@/components/Footer';
import { MedioCard } from '@/components/MedioCard';
import { PageHeader } from '@/components/PageHeader';
import { getMedios } from '@/lib/get-medios';

export const dynamic = 'force-dynamic';

export default async function MediosPage() {
  const medios = await getMedios();

  return (
    <div>
      <PageHeader />

      <p className="pa-page-intro">
        Un mapa de referencia de la orientación editorial de los principales medios
        argentinos citados en este sitio. Es una caracterización propia, no una
        medición objetiva — se basa en la línea editorial histórica de cada medio y su
        pertenencia a un grupo mediático (mismo espíritu que los &quot;media bias
        charts&quot; de sitios como AllSides o Ad Fontes Media). Se puede estar en
        desacuerdo con alguna ubicación; si algo cambió o te parece que está mal
        clasificado, es un criterio editorial que se revisa, no un dato cerrado.
      </p>

      {medios === null && (
        <p className="pa-page-intro">No se pudo conectar con el backend para traer el listado de medios.</p>
      )}
      {medios !== null && medios.length === 0 && (
        <p className="pa-page-intro">Todavía no hay medios cargados.</p>
      )}

      {medios && medios.length > 0 && (
        <div className="pa-medios-grid">
          {medios.map((m) => (
            <MedioCard key={m.id} medio={m} />
          ))}
        </div>
      )}

      <Footer />
    </div>
  );
}
