import type { CategoriaVM } from '@/lib/types';
import { CategoriaIcon } from './icon-map';

export function NavCategorias({
  categorias,
  activeCat,
  onChange,
}: {
  categorias: CategoriaVM[];
  activeCat: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="pa-nav">
      {categorias.map((c) => (
        <button
          key={c.id}
          className={`pa-nav-btn ${activeCat === c.id ? 'active' : ''}`}
          onClick={() => onChange(c.id)}
        >
          <CategoriaIcon nombre={c.icono} size={15} />
          {c.nombre}
        </button>
      ))}
    </div>
  );
}
