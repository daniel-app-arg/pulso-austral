'use client';

import { useState } from 'react';
import type { PulsoIndexDTO, PulsoIndexDetalleDTO } from '@/lib/types';
import { TrendIcon } from './TrendIcon';

function estadoDe(score: number): { label: string; color: string } {
  if (score >= 60) return { label: 'Mejorando', color: 'var(--teal)' };
  if (score <= 40) return { label: 'Empeorando', color: 'var(--brick)' };
  return { label: 'Estable', color: 'var(--ochre)' };
}

const ICONO_DIRECCION = { mejora: 'up', empeora: 'down', sin_cambio: 'flat' } as const;

function ListaDetalle({ detalle }: { detalle: PulsoIndexDetalleDTO[] }) {
  return (
    <div className="pa-pulso-lista">
      {detalle.map((d) => (
        <span className="pa-pulso-item" key={d.id}>
          <TrendIcon trend={ICONO_DIRECCION[d.direccion]} size={12} />
          <b>{d.nombre}</b>
        </span>
      ))}
    </div>
  );
}

export function PulsoIndexBanner({ data }: { data: PulsoIndexDTO }) {
  const [abierto, setAbierto] = useState(false);
  const { corto_plazo: cortoPlazo, mandato } = data;
  const estadoCorto = estadoDe(cortoPlazo.score);
  const estadoMandato = mandato?.score !== null && mandato ? estadoDe(mandato.score) : null;

  return (
    <div className="pa-pulso-banner" style={{ '--estado-color': estadoCorto.color } as React.CSSProperties}>
      <div className="pa-pulso-doble">
        <div className="pa-pulso-inner pa-pulso-mitad">
          <div className="pa-pulso-score">{Math.round(cortoPlazo.score)}</div>
          <div className="pa-pulso-texto">
            <div className="pa-pulso-titulo">
              <span className="pa-pulso-subtitulo">Últimos 30 días</span>
              <span className="pa-pulso-estado">{estadoCorto.label}</span>
              {cortoPlazo.trend && cortoPlazo.delta !== null && (
                <span className="pa-pulso-delta">
                  <TrendIcon trend={cortoPlazo.trend} size={12} />
                  {cortoPlazo.delta >= 0 ? '+' : ''}
                  {cortoPlazo.delta.toFixed(1)} desde la foto anterior
                </span>
              )}
            </div>
            <div className="pa-pulso-desglose">
              {cortoPlazo.mejorando} de {cortoPlazo.total} indicadores comparables mejoran,{' '}
              {cortoPlazo.empeorando} empeoran, {cortoPlazo.sin_cambio} sin cambio.
            </div>
          </div>
        </div>

        <div className="pa-pulso-separador" />

        <div
          className="pa-pulso-inner pa-pulso-mitad"
          style={{ '--estado-color': estadoMandato?.color ?? 'var(--ochre)' } as React.CSSProperties}
        >
          {mandato && estadoMandato ? (
            <>
              <div className="pa-pulso-score" style={{ color: estadoMandato.color }}>
                {Math.round(mandato.score!)}
              </div>
              <div className="pa-pulso-texto">
                <div className="pa-pulso-titulo">
                  <span className="pa-pulso-subtitulo">Mandato de {mandato.gobierno.presidente.split(' (')[0]}</span>
                  <span className="pa-pulso-estado" style={{ color: estadoMandato.color }}>
                    {estadoMandato.label}
                  </span>
                </div>
                <div className="pa-pulso-desglose">
                  {mandato.mejorando} de {mandato.total} indicadores comparables mejoraron desde el inicio del
                  mandato, {mandato.empeorando} empeoraron, {mandato.sin_cambio} sin cambio.
                </div>
              </div>
            </>
          ) : (
            <div className="pa-pulso-texto">
              <div className="pa-pulso-desglose">Todavía no hay indicadores comparables para el mandato actual.</div>
            </div>
          )}
        </div>

        <button className="pa-pulso-toggle" onClick={() => setAbierto((a) => !a)}>
          {abierto ? 'Ocultar metodología' : '¿Cómo se calcula?'}
        </button>
      </div>

      {abierto && (
        <div className="pa-pulso-detalle">
          <p className="pa-pulso-metodologia">
            Son dos números, cada uno sobre una ventana de tiempo distinta — no un promedio ponderado de unidades
            distintas (%, pb, US$ B...), sino un índice de difusión: 50 + 50 × (mejoran − empeoran) / total. 50 es
            tantos mejorando como empeorando, 100 es todos mejorando, 0 es todos empeorando.
            <br />
            <b>Últimos 30 días</b> compara cada indicador al principio y al final de ese período — el pulso de corto
            plazo, se recalcula todos los días.
            <br />
            <b>Mandato actual</b> compara cada indicador el día que asumió el gobierno en curso contra hoy — mientras
            el mandato siga en curso este número se sigue moviendo; una vez que termine queda fijo (se puede
            consultar en &quot;Por gobierno&quot; para cualquier gestión anterior).
            <br />
            En los dos casos se cuentan solo los indicadores donde hay consenso amplio sobre qué dirección es una
            mejora. Quedan afuera a propósito los que no lo tienen — dólar, Merval, todo lo de desarrollo militar,
            aprobación y confianza en el gobierno, gasto público, y canasta básica (nominal, siempre sube con
            inflación) — meterlos obligaría a asumir una postura ideológica disfrazada de medición objetiva.
          </p>
          <div className="pa-pulso-detalle-columnas">
            <div>
              <div className="pa-pulso-detalle-titulo">Últimos 30 días</div>
              <ListaDetalle detalle={cortoPlazo.detalle} />
            </div>
            {mandato && (
              <div>
                <div className="pa-pulso-detalle-titulo">Mandato actual</div>
                <ListaDetalle detalle={mandato.detalle} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
