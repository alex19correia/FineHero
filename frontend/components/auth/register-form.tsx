'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import Button from '../ui/button';
import Input from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import { superheroToast } from '../superhero/superhero-toast';

const registerSchema = z.object({
  fullName: z.string().min(3, { message: 'O nome completo deve ter pelo menos 3 caracteres.' }),
  email: z.string().email({ message: 'Por favor, insira um email válido.' }),
  password: z.string().min(6, { message: 'A senha deve ter pelo menos 6 caracteres.' }),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterForm() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: RegisterFormValues) => api.post('/api/v1/auth/register', data),
    onSuccess: (data) => {
      localStorage.setItem('finehero_token', data.data.token);
      superheroToast.success('Conta criada com sucesso!');
      router.push('/dashboard');
    },
    onError: (error: any) => {
      superheroToast.error(error.response?.data?.message || 'Ocorreu um erro ao criar a conta.');
    },
  });

  const onSubmit = (data: RegisterFormValues) => {
    mutation.mutate(data);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Criar conta gratuita</CardTitle>
        <CardDescription>Junte-se ao FineHero e comece a contestar as suas multas!</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            id="fullName"
            label="Nome Completo"
            type="text"
            {...register('fullName')}
            error={errors.fullName?.message}
          />
          <Input
            id="email"
            label="Email"
            type="email"
            {...register('email')}
            error={errors.email?.message}
          />
          <Input
            id="password"
            label="Senha"
            type="password"
            {...register('password')}
            error={errors.password?.message}
          />
          <Button type="submit" className="w-full" isLoading={mutation.isPending}>
            Criar Conta
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
