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

      <div className="pa-acerca">
        <div className="pa-acerca-titulo">Acerca de este sitio</div>
        <ul className="pa-acerca-lista">
          <li>
            <b>Qué es.</b> Pulso Austral es un proyecto independiente, sin afiliación partidaria ni
            gubernamental. No representa a ningún gobierno, partido ni organización.
          </li>
          <li>
            <b>Cómo se tratan las fuentes.</b> Cada indicador cita su fuente real (INDEC, BCRA y
            otros organismos y encuestadoras). Cuando no se encuentra un dato verificable, el
            campo se muestra vacío — nunca se inventa un número para que &quot;se vea completo&quot;.
          </li>
          <li>
            <b>Investigación asistida por IA.</b> Buena parte de las series históricas de este
            sitio se compiló con ayuda de investigación asistida por IA, contrastando fuentes
            públicas. Es un proceso con verificación, no infalible — pueden colarse errores de
            interpretación. Si encontrás uno, avisá para corregirlo.
          </li>
          <li>
            <b>Estimaciones propias.</b> Algunos valores (por ejemplo, salario real de meses sin
            una cifra oficial directa) son cálculos propios a partir de series oficiales — nominal
            menos inflación del mismo período. Se marcan como &quot;estimado&quot; o &quot;calculado&quot; en la
            nota de cada dato, para distinguirlos de una cifra publicada tal cual por el organismo.
          </li>
          <li>
            <b>La bitácora oficial del Gobierno.</b> Algunas noticias y eventos de la línea de
            tiempo citan como fuente la &quot;Bitácora de gestión&quot; del Poder Ejecutivo Nacional
            (argentina.gob.ar). No es periodismo independiente: es comunicación oficial del
            gobierno sobre su propia gestión, sin cobertura de hechos negativos ni contrapunto —
            por eso se etiqueta aparte del resto de las fuentes. Ver la página{' '}
            <a href="/medios">Medios</a> para la caracterización de cada fuente.
          </li>
        </ul>
      </div>

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
