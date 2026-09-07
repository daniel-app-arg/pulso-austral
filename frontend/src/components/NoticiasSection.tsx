import { Newspaper } from 'lucide-react';
import type { NoticiaVM } from '@/lib/types';

export function NoticiasSection({ noticias, nombreCategoria }: { noticias: NoticiaVM[]; nombreCategoria: string }) {
  return (
    <>
      <div className="pa-section-title">
        <Newspaper size={18} />
        Noticias de {nombreCategoria}
      </div>
      <div className="pa-noticias">
        {noticias.length === 0 && <div className="pa-noticias-vacio">Todavía no hay noticias cargadas para esta categoría.</div>}
        {noticias.map((n, i) => (
          <div className="pa-noticia" key={i}>
            <span className="pa-noticia-kicker">{n.kicker}</span>
            <span className="pa-noticia-fecha"> · {n.fecha}</span>
            <div className="pa-noticia-titulo">{n.titulo}</div>
            <div className="pa-noticia-bajada">{n.bajada}</div>
            {n.medio && (
              n.url ? (
                <a className="pa-noticia-fuente" href={n.url} target="_blank" rel="noopener noreferrer">
                  fuente: {n.medio} ↗
                </a>
              ) : (
                <span className="pa-noticia-fuente">fuente: {n.medio}</span>
              )
            )}
          </div>
        ))}
      </div>
    </>
  );
}
