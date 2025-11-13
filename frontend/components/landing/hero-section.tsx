import Button from '../ui/button';
import Link from 'next/link';
import HeroCharacter from '../superhero/hero-character';
import AnimationSequence from '../superhero/animation-sequence';

export default function HeroSection() {
  return (
    <section className="bg-gray-50">
      <div className="container mx-auto px-6 py-16 text-center">
        <div className="mx-auto max-w-lg">
          <h1 className="text-3xl font-bold text-gray-800 md:text-4xl">
            Recorrer a tua multa em minutos — carta pronta e fundamentada em lei
          </h1>
          <p className="mt-6 text-gray-600">
            Gera uma carta formal, com artigos do Código da Estrada citados, em 3 minutos. PDF
            pronto para enviar. Sem advogados caros.
          </p>
          <div className="mt-8 space-y-4">
            <p className="flex items-center justify-center text-gray-700">
              <svg
                className="mr-2 h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M5 13l4 4L19 7"
                ></path>
              </svg>
              Carta personalizada com referência a artigos legais relevantes.
            </p>
            <p className="flex items-center justify-center text-gray-700">
              <svg
                className="mr-2 h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M5 13l4 4L19 7"
                ></path>
              </svg>
              PDF pronto para imprimir ou enviar por email/Portal das Contraordenações.
            </p>
            <p className="flex items-center justify-center text-gray-700">
              <svg
                className="mr-2 h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M5 13l4 4L19 7"
                ></path>
              </svg>
              Beta: 1 recurso grátis — subscrição mensal desde €7,90 para uso ilimitado.
            </p>
          </div>
          <Link href="/register">
            <Button className="mt-8" size="lg">
              Gerar carta grátis
            </Button>
          </Link>
        </div>
        <div className="mt-12">
          <AnimationSequence>
            <HeroCharacter />
          </AnimationSequence>
        </div>
      </div>
    </section>
  );
}
