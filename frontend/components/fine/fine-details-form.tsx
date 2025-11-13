'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import Button from '../ui/button';
import Input from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const fineDetailsSchema = z.object({
  incident_date: z.string().nonempty({ message: 'A data do incidente é obrigatória.' }),
  incident_time: z.string().optional(),
  location: z.string().nonempty({ message: 'O local é obrigatório.' }),
  fine_type: z.string().nonempty({ message: 'O tipo de multa é obrigatório.' }),
  fine_amount: z.preprocess(
    (a) => parseFloat(z.string().parse(a)),
    z.number().positive({ message: 'O valor da multa deve ser positivo.' })
  ),
  incident_description: z
    .string()
    .nonempty({ message: 'A descrição do incidente é obrigatória.' }),
});

type FineDetailsFormValues = z.infer<typeof fineDetailsSchema>;

export default function FineDetailsForm({ fineId }: { fineId: string }) {
  const router = useRouter();
  const { data: fine, isLoading } = useQuery({
    queryKey: ['fine', fineId],
    queryFn: () => api.get(`/api/v1/fines/${fineId}`).then((res) => res.data),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FineDetailsFormValues>({
    resolver: zodResolver(fineDetailsSchema),
  });

  useEffect(() => {
    if (fine) {
      reset({
        ...fine,
        incident_date: fine.incident_date.split('T')[0],
      });
    }
  }, [fine, reset]);

  const mutation = useMutation({
    mutationFn: (data: FineDetailsFormValues) => api.put(`/api/v1/fines/${fineId}`, data),
    onSuccess: () => {
      router.push(`/fine/${fineId}/generate`);
    },
  });

  const onSubmit = (data: FineDetailsFormValues) => {
    mutation.mutate(data);
  };

  if (isLoading) {
    return <div>A carregar...</div>;
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Detalhes da Multa</CardTitle>
        <CardDescription>
          Preencha os detalhes da sua multa para que o FineHero possa gerar a sua defesa.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <Input
              id="incident_date"
              label="Data do Incidente"
              type="date"
              {...register('incident_date')}
              error={errors.incident_date?.message}
            />
            <Input
              id="incident_time"
              label="Hora do Incidente"
              type="time"
              {...register('incident_time')}
              error={errors.incident_time?.message}
            />
          </div>
          <Input
            id="location"
            label="Local"
            type="text"
            {...register('location')}
            error={errors.location?.message}
          />
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <Input
              id="fine_type"
              label="Tipo de Multa"
              type="text"
              {...register('fine_type')}
              error={errors.fine_type?.message}
            />
            <Input
              id="fine_amount"
              label="Valor da Multa (€)"
              type="number"
              step="0.01"
              {...register('fine_amount')}
              error={errors.fine_amount?.message}
            />
          </div>
          <div>
            <label htmlFor="incident_description" className="mb-1 block text-sm font-medium">
              Descrição do Incidente
            </label>
            <textarea
              id="incident_description"
              {...register('incident_description')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-finehero-primary focus:ring-finehero-primary sm:text-sm"
              rows={4}
            />
            {errors.incident_description && (
              <p className="mt-2 text-sm text-red-600">{errors.incident_description.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" isLoading={mutation.isPending}>
            Gerar Defesa
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
