import { LogoMark } from './LogoMark';
import { SiteNav } from './SiteNav';

/** Encabezado liviano para páginas que no son el dashboard principal
 * (Medios, Por gobierno, Glosario): título + tagline + navegación del
 * sitio, sin el bloque de dólares/ticker (eso es específico del home). */
export function PageHeader() {
  return (
    <div className="pa-masthead" style={{ paddingBottom: 4 }}>
      <div className="pa-masthead-top">
        <div className="pa-brand">
          <LogoMark size={34} />
          <div>
            <h1 className="pa-title pa-serif">Pulso Austral</h1>
            <div className="pa-tagline">El estado del país, medido.</div>
          </div>
        </div>
      </div>
      <SiteNav />
    </div>
  );
}
