import Button from '../ui/button';
import Link from 'next/link';

export default function SubscriptionPlans() {
  return (
    <div className="grid gap-8 md:grid-cols-2">
      <div className="rounded-lg border border-gray-200 p-8 shadow-md">
        <h3 className="text-xl font-bold text-gray-800">Pagamento Único</h3>
        <p className="mt-4 text-5xl font-bold text-gray-800">€25</p>
        <p className="mt-2 text-gray-600">por carta</p>
        <ul className="mt-6 space-y-4 text-gray-600">
          <li>Geração automática</li>
          <li>Baseado em legislação</li>
          <li>Suporte por email</li>
        </ul>
        <Link href="/payment?plan=single">
          <Button className="mt-8" variant="secondary">
            Pagar
          </Button>
        </Link>
      </div>
      <div className="rounded-lg border-2 border-finehero-primary p-8 shadow-xl">
        <h3 className="text-xl font-bold text-gray-800">Pro</h3>
        <p className="mt-4 text-5xl font-bold text-gray-800">€15</p>
        <p className="mt-2 text-gray-600">por mês</p>
        <ul className="mt-6 space-y-4 text-gray-600">
          <li>Cartas ilimitadas</li>
          <li>Geração automática</li>
          <li>Baseado em legislação</li>
          <li>Suporte prioritário</li>
        </ul>
        <Link href="/payment?plan=pro">
          <Button className="mt-8">Subscrever</Button>
        </Link>
      </div>
    </div>
  );
}
