'use client';

import Button from '@/components/ui/button';
import Link from 'next/link';
import HeroCharacter from '@/components/superhero/hero-character';

export default function PaymentSuccessPage() {
  return (
    <div className="container mx-auto px-6 py-16 text-center">
      <HeroCharacter />
      <h1 className="mt-8 text-3xl font-bold text-gray-800 md:text-4xl">
        A defesa está pronta, SUPERHERO em ação! 💪
      </h1>
      <p className="mt-6 text-gray-600">
        O teu pagamento foi processado com sucesso. O FineHero resgatou-te de mais uma multa!
      </p>
      <div className="mt-8">
        <Link href="/dashboard">
          <Button size="lg">Ver as minhas multas</Button>
        </Link>
      </div>
    </div>
  );
}
