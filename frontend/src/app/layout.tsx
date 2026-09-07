import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Pulso Austral',
  description: 'El estado del país, medido. Dashboard de indicadores económicos, sociales y geopolíticos de Argentina.',
};

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
