'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  useStripe,
  useElements,
  PaymentElement,
  Elements,
} from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import Button from '../ui/button';
import { useState } from 'react';
import { superheroToast } from '../superhero/superhero-toast';

const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || ''
);

const CheckoutForm = ({ clientSecret }: { clientSecret: string }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsLoading(true);

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/payment/success`,
      },
    });

    if (error) {
      superheroToast.error(error.message || 'Ocorreu um erro ao processar o pagamento.');
    }

    setIsLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <Button type="submit" className="mt-4 w-full" isLoading={isLoading} disabled={!stripe}>
        Pagar
      </Button>
    </form>
  );
};

export default function PaymentForm({
  clientSecret,
  plan,
  amount,
}: {
  clientSecret: string;
  plan: string;
  amount: number;
}) {
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Pagamento</CardTitle>
        <CardDescription>
          Estás a um passo de ter a tua defesa pronta. O FineHero está contigo!
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <p className="font-bold">{plan}</p>
          <p className="text-2xl font-bold">€{amount}</p>
        </div>
        <Elements stripe={stripePromise} options={{ clientSecret }}>
          <CheckoutForm clientSecret={clientSecret} />
        </Elements>
      </CardContent>
    </Card>
  );
}
