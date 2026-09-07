'use client';

import { useState } from 'react';
import type { DashboardData, IndicadorVM, PulsoIndexDTO } from '@/lib/types';
import { Masthead } from './Masthead';
import { NavCategorias } from './NavCategorias';
import { PanelIndicadores } from './PanelIndicadores';
import { PulsoIndexBanner } from './PulsoIndexBanner';
import { TimelineSection } from './TimelineSection';
import { NoticiasSection } from './NoticiasSection';
import { Footer } from './Footer';
import { IndicadorModal } from './IndicadorModal';

export function Dashboard({ data, pulsoIndex }: { data: DashboardData; pulsoIndex: PulsoIndexDTO | null }) {
  const { categorias, timeline, noticias, destacados, ticker, fuenteDatos } = data;
  const [activeCat, setActiveCat] = useState(categorias[0]?.id ?? '');
  const [indicadorExpandido, setIndicadorExpandido] = useState<IndicadorVM | null>(null);

  const cat = categorias.find((c) => c.id === activeCat) ?? categorias[0];
  const noticiasFiltradas = noticias.filter((n) => n.categoria === activeCat);

  if (!cat) {
    return <div className="pa-footer">No hay categorías cargadas.</div>;
  }

  return (
    <div>
      {pulsoIndex && <PulsoIndexBanner data={pulsoIndex} />}

      <Masthead destacados={destacados} ticker={ticker} fuenteDatos={fuenteDatos} />

      <NavCategorias categorias={categorias} activeCat={activeCat} onChange={setActiveCat} />

      <PanelIndicadores categoria={cat} onAbrirIndicador={setIndicadorExpandido} />

      <TimelineSection timeline={timeline} />

      <NoticiasSection noticias={noticiasFiltradas} nombreCategoria={cat.nombre} />

      <Footer />

      {indicadorExpandido && (
        <IndicadorModal
          indicador={indicadorExpandido}
          color={cat.color}
          onCerrar={() => setIndicadorExpandido(null)}
        />
      )}
    </div>
  );
}
