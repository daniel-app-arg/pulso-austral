'use client';

import { useMemo, useState } from 'react';
import type { CategoriaDTO, GobiernoResumenDTO, ResumenIndicadorDTO } from '@/lib/types';
import { fechaCortaConAnio } from '@/lib/format';
import { IndiceGeneralGobierno } from './IndiceGeneralGobierno';
import { TrendIcon } from './TrendIcon';

function formatNumero(valor: number, decimales = 2): string {
  return valor.toLocaleString('es-AR', { maximumFractionDigits: decimales });
}

function formatValor(valor: number | string | null | undefined, unidad: string): string {
  if (valor === null || valor === undefined) return '—';
  if (typeof valor === 'string') return valor;
  return `${formatNumero(valor)}${unidad ? ' ' + unidad : ''}`;
}

function FilaIndicador({ ind }: { ind: ResumenIndicadorDTO }) {
  if (ind.sin_datos) {
    return (
      <tr>
        <td className="pa-gob-nombre">{ind.nombre}</td>
        <td className="pa-gob-sin-datos" colSpan={3}>
          sin datos cargados para este período
        </td>
      </tr>
    );
  }

  const esCualitativo = ind.tipo === 'cualitativo';
  const trend = !esCualitativo && ind.variacion_abs != null
    ? (ind.variacion_abs > 0 ? 'up' : ind.variacion_abs < 0 ? 'down' : 'flat')
    : null;
  // Si el indicador ya es un porcentaje, la diferencia se expresa en puntos
  // porcentuales (pp) — repetir "%" sobre una diferencia de porcentajes
  // confunde cambio absoluto con cambio relativo (mismo criterio que ya
  // usa el backend en _con_deltas_pp).
  const unidadVariacion = ind.unidad === '%' ? 'pp' : ind.unidad;

  return (
    <tr>
      <td className="pa-gob-nombre">{ind.nombre}</td>
      <td>{formatValor(ind.valor_inicio, ind.unidad)}</td>
      <td>{formatValor(ind.valor_fin, ind.unidad)}</td>
      <td>
        {esCualitativo || ind.variacion_abs == null ? (
          '—'
        ) : (
          <span className="pa-gob-variacion">
            <TrendIcon trend={trend ?? 'flat'} polaridad={ind.polaridad} size={12} />
            {ind.variacion_abs >= 0 ? '+' : ''}
            {formatNumero(ind.variacion_abs)}
            {unidadVariacion ? ` ${unidadVariacion}` : ''}
            {ind.variacion_pct != null && (
              <span>({ind.variacion_pct >= 0 ? '+' : ''}{formatNumero(ind.variacion_pct, 1)}%)</span>
            )}
          </span>
        )}
      </td>
    </tr>
  );
}

export function GobiernosComparativa({
  categorias,
  resumenes,
}: {
  categorias: CategoriaDTO[];
  resumenes: GobiernoResumenDTO[];
}) {
  const [seleccionado, setSeleccionado] = useState(resumenes.length - 1);
  const resumen = resumenes[seleccionado];

  const porCategoria = useMemo(() => {
    const mapa = new Map<string, ResumenIndicadorDTO[]>();
    resumen.indicadores.forEach((ind) => {
      const lista = mapa.get(ind.categoria_id) ?? [];
      lista.push(ind);
      mapa.set(ind.categoria_id, lista);
    });
    return mapa;
  }, [resumen]);

  const enCurso = !resumen.gobierno.fecha_fin;

  return (
    <div>
      <div className="pa-gob-selector">
        {resumenes.map((r, i) => (
          <button
            key={r.gobierno.id}
            className={`pa-gob-btn ${i === seleccionado ? 'active' : ''}`}
            onClick={() => setSeleccionado(i)}
          >
            {r.gobierno.presidente.split(' (')[0]}
          </button>
        ))}
      </div>

      <p className="pa-gob-periodo">
        {resumen.gobierno.partido && <>{resumen.gobierno.partido} · </>}
        {fechaCortaConAnio(resumen.desde)} — {enCurso ? 'en curso' : fechaCortaConAnio(resumen.hasta)}
      </p>

      <IndiceGeneralGobierno data={resumen.indice_general} enCurso={enCurso} />

      <div className="pa-gob-table-wrap">
        {categorias.map((cat) => {
          const indicadores = porCategoria.get(cat.id);
          if (!indicadores || indicadores.length === 0) return null;
          return (
            <table className="pa-gob-table" key={cat.id}>
              <caption>{cat.nombre}</caption>
              <thead>
                <tr>
                  <th>Indicador</th>
                  <th>Al inicio</th>
                  <th>Al final</th>
                  <th>Variación</th>
                </tr>
              </thead>
              <tbody>
                {indicadores.map((ind) => (
                  <FilaIndicador ind={ind} key={ind.id} />
                ))}
              </tbody>
            </table>
          );
        })}
      </div>
    </div>
  );
}
