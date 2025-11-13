import Button from '../ui/button';
import Link from 'next/link';

export default function PricingSection() {
  return (
    <section id="precos" className="bg-white py-16">
      <div className="container mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold text-gray-800">Preços</h2>
        <div className="mt-8 grid gap-8 md:grid-cols-3">
          <div className="rounded-lg border border-gray-200 p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">Grátis (Beta)</h3>
            <p className="mt-4 text-5xl font-bold text-gray-800">€0</p>
            <p className="mt-2 text-gray-600">1 carta grátis</p>
            <ul className="mt-6 space-y-4 text-gray-600">
              <li>Geração automática</li>
              <li>Baseado em legislação</li>
              <li>Suporte por email</li>
            </ul>
            <Link href="/register">
              <Button className="mt-8" variant="secondary">
                Começar
              </Button>
            </Link>
          </div>
          <div className="rounded-lg border-2 border-finehero-primary p-8 shadow-xl">
            <h3 className="text-xl font-bold text-gray-800">Pro</h3>
            <p className="mt-4 text-5xl font-bold text-gray-800">€7,90</p>
            <p className="mt-2 text-gray-600">por mês</p>
            <ul className="mt-6 space-y-4 text-gray-600">
              <li>Cartas ilimitadas</li>
              <li>Geração automática</li>
              <li>Baseado em legislação</li>
              <li>Suporte prioritário</li>
            </ul>
            <Link href="/register">
              <Button className="mt-8">Subscrever</Button>
            </Link>
          </div>
          <div className="rounded-lg border border-gray-200 p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">Premium</h3>
            <p className="mt-4 text-5xl font-bold text-gray-800">€79</p>
            <p className="mt-2 text-gray-600">por carta</p>
            <ul className="mt-6 space-y-4 text-gray-600">
              <li>Revisão por advogado</li>
              <li>Assinatura por advogado</li>
              <li>Garantia de submissão</li>
              <li>Suporte por telefone</li>
            </ul>
            <Link href="/register">
              <Button className="mt-8" variant="secondary">
                Saber mais
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
