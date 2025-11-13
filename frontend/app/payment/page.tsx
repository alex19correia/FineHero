'use client';

import PaymentForm from '@/components/payment/payment-form';
import SubscriptionPlans from '@/components/payment/subscription-plans';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export default function PaymentPage() {
  const searchParams = useSearchParams();
  const plan = searchParams.get('plan');
  const fineId = searchParams.get('fineId');

  const { data, isLoading } = useQuery({
    queryKey: ['paymentIntent', plan, fineId],
    queryFn: async () => {
      if (plan === 'single') {
        const res = await api.post('/api/v1/payments/one-time', { fineId });
        return { ...res.data, amount: 25, plan: 'Pagamento Único' };
      } else {
        const res = await api.post('/api/v1/payments/subscribe', { plan });
        return { ...res.data, amount: 15, plan: 'Subscrição Pro' };
      }
    },
    enabled: !!plan,
  });

  if (isLoading) {
    return <div>A carregar...</div>;
  }

  return (
    <div className="container mx-auto px-6 py-16">
      <div className="flex flex-col items-center justify-center">
        {plan ? (
          data && (
            <PaymentForm
              clientSecret={data.clientSecret}
              plan={data.plan}
              amount={data.amount}
            />
          )
        ) : (
          <SubscriptionPlans />
        )}
      </div>
    </div>
  );
}
