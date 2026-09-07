import type { OrientacionPolitica } from '@/lib/types';

const POSICIONES: Record<OrientacionPolitica, number> = {
  izquierda: 0,
  centro_izquierda: 1,
  centro: 2,
  centro_derecha: 3,
  derecha: 4,
};

const ETIQUETAS: Record<OrientacionPolitica, string> = {
  izquierda: 'Izquierda',
  centro_izquierda: 'Centro-izquierda',
  centro: 'Centro',
  centro_derecha: 'Centro-derecha',
  derecha: 'Derecha',
};

/** Posición en una escala izquierda-derecha, con un punto marcado — a
 * propósito sin colores por bloque político (para no sugerir un juicio de
 * valor): un solo acento neutro marca dónde cae cada medio. */
export function OrientacionScale({ orientacion }: { orientacion: OrientacionPolitica }) {
  const posicion = POSICIONES[orientacion] ?? 2;
  return (
    <div className="pa-orientacion">
      <div className="pa-orientacion-track">
        {[0, 1, 2, 3, 4].map((i) => (
          <span key={i} className={`pa-orientacion-tick ${i === posicion ? 'active' : ''}`} />
        ))}
      </div>
      <span className="pa-orientacion-label">{ETIQUETAS[orientacion] ?? orientacion}</span>
    </div>
  );
}
