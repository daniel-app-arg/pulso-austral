import type { MedioDTO } from '@/lib/types';
import { OrientacionScale } from './OrientacionScale';

const NOMBRE_TIPO: Record<MedioDTO['tipo'], string> = {
  diario: 'Diario / digital',
  agencia: 'Agencia',
  tv: 'Televisión',
  radio: 'Radio',
  revista: 'Revista',
  factchecking: 'Verificación de datos',
};

export function MedioCard({ medio }: { medio: MedioDTO }) {
  return (
    <div className="pa-medio-card">
      <div className="pa-medio-header">
        <a className="pa-medio-nombre" href={medio.url} target="_blank" rel="noopener noreferrer">
          {medio.nombre}
        </a>
        <span className="pa-medio-tipo">{NOMBRE_TIPO[medio.tipo] ?? medio.tipo}</span>
      </div>
      <OrientacionScale orientacion={medio.orientacion} />
      <p className="pa-medio-descripcion">{medio.descripcion}</p>
    </div>
  );
}
