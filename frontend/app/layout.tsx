import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import MSWComponent from './msw-component';
import QueryProvider from './query-provider';
import Navbar from '@/components/layout/navbar';
import Footer from '@/components/layout/footer';
import { SuperheroToaster } from '@/components/superhero/superhero-toast';
import GoogleAnalytics from '@/components/layout/google-analytics';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'FineHero - O seu super-herói contra as multas',
  description:
    'Gere defesas para multas de trânsito em minutos com a ajuda da inteligência artificial. O FineHero é a sua arma secreta para contestar multas de forma rápida e eficaz.',
  keywords: [
    'recorrer multa',
    'contestar multa',
    'contestar multa estacionamento',
    'recurso multa estacionamento',
    'recorrer multa velocidade',
    'contestar coima',
    'como recorrer multa',
    'carta recurso multa',
    'recurso contraordenação trânsito',
    'recorrer coima estacionamento',
    'modelo carta recurso multa estacionamento',
    'como contestar multa radar portugal',
  ],
  openGraph: {
    title: 'FineHero - Recorrer Multa em 3 Minutos',
    description: 'Gera carta de recurso com artigos do Código da Estrada. 1 carta grátis.',
    url: 'https://finehero.pt',
    siteName: 'FineHero',
    images: [
      {
        url: 'https://finehero.pt/og-image.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'pt_PT',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'FineHero - Recorrer Multa em 3 Minutos',
    description: 'Gera carta de recurso com artigos do Código da Estrada. 1 carta grátis.',
    images: ['https://finehero.pt/twitter-image.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-PT">
      <body className={`${inter.className} flex flex-col min-h-screen`}>
        <MSWComponent>
          <QueryProvider>
            <GoogleAnalytics />
            <SuperheroToaster />
            <Navbar />
            <main className="flex-grow">{children}</main>
            <Footer />
          </QueryProvider>
        </MSWComponent>
      </body>
    </html>
  );
}
