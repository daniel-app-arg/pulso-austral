import { Factory, Gauge, Globe2, HeartPulse, Landmark, Scale, Shield, Swords, TrendingUp, Users, type LucideIcon } from 'lucide-react';

// Mapea el nombre de ícono guardado en Categoria.icono (Django) al
// componente lucide-react real — mismo mapeo que ICONOS_DB en el artifact.
export const ICONOS: Record<string, LucideIcon> = {
  Landmark,
  Users,
  Globe2,
  Scale,
  Factory,
  TrendingUp,
  HeartPulse,
  Gauge,
  Shield,
  Swords,
};

export function CategoriaIcon({ nombre, size = 15 }: { nombre: string; size?: number }) {
  const Icon = ICONOS[nombre] || Landmark;
  return <Icon size={size} />;
}
