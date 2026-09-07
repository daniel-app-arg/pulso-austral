import type { CategoriaVM, IndicadorVM } from '@/lib/types';
import { IndicadorCard } from './IndicadorCard';

export function PanelIndicadores({
  categoria,
  onAbrirIndicador,
}: {
  categoria: CategoriaVM;
  onAbrirIndicador: (indicador: IndicadorVM) => void;
}) {
  return (
    <div className="pa-panel">
      <div className="pa-grid">
        {categoria.indicadores.map((ind) => (
          <IndicadorCard key={ind.id} indicador={ind} color={categoria.color} onAbrir={onAbrirIndicador} />
        ))}
      </div>
    </div>
  );
}
