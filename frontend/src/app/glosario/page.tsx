import { Footer } from '@/components/Footer';
import { PageHeader } from '@/components/PageHeader';
import { getGlosario } from '@/lib/get-glosario';

export const dynamic = 'force-dynamic';

export default async function GlosarioPage() {
  const data = await getGlosario();

  return (
    <div>
      <PageHeader />

      <p className="pa-page-intro">
        Qué mide cada indicador del dashboard y de dónde sale, en una frase. Los que todavía no
        tienen metodología documentada lo dicen explícitamente — mejor eso que inventar un texto.
      </p>

      {data === null && (
        <p className="pa-page-intro">No se pudo conectar con el backend para traer el glosario.</p>
      )}

      {data && data.categorias.map((cat) => {
        const indicadores = data.indicadores.filter((i) => i.categoria_id === cat.id);
        if (indicadores.length === 0) return null;
        return (
          <div key={cat.id}>
            <div className="pa-glosario-categoria" style={{ '--cat-color': cat.color } as React.CSSProperties}>
              {cat.nombre}
            </div>
            <div className="pa-glosario-lista">
              {indicadores.map((ind) => (
                <div className="pa-glosario-item" key={ind.id}>
                  <div className="pa-glosario-cabecera">
                    <span className="pa-glosario-nombre">{ind.nombre}</span>
                    {ind.unidad && <span className="pa-glosario-unidad">({ind.unidad})</span>}
                  </div>
                  {ind.metodologia ? (
                    <p className="pa-glosario-texto">{ind.metodologia}</p>
                  ) : (
                    <p className="pa-glosario-texto pa-glosario-pendiente">
                      Metodología todavía no documentada.
                    </p>
                  )}
                  {ind.fuente && (
                    <a className="pa-glosario-fuente" href={ind.fuente.url} target="_blank" rel="noopener noreferrer">
                      fuente: {ind.fuente.nombre} ↗
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      <Footer />
    </div>
  );
}
