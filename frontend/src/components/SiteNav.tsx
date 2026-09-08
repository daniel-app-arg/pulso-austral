'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Coffee } from 'lucide-react';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/medios', label: 'Medios' },
  { href: '/gobiernos', label: 'Por gobierno' },
  { href: '/glosario', label: 'Glosario' },
];

// TODO: reemplazar por el link real de Cafecito cuando exista la cuenta
// (cafecito.app/<usuario>) — hasta entonces queda como placeholder, no
// lleva a ningún lado todavía.
const LINK_APOYO = 'https://cafecito.app/pulsoaustral';

export function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="pa-sitenav">
      {LINKS.map((l) => (
        <Link key={l.href} href={l.href} className={pathname === l.href ? 'active' : ''}>
          {l.label}
        </Link>
      ))}
      <a href={LINK_APOYO} target="_blank" rel="noopener noreferrer" className="pa-sitenav-apoyo">
        <Coffee size={14} />
        Apoyá este proyecto
      </a>
    </nav>
  );
}
