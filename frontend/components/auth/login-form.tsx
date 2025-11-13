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

const loginSchema = z.object({
  email: z.string().email({ message: 'Por favor, insira um email válido.' }),
  password: z.string().min(6, { message: 'A senha deve ter pelo menos 6 caracteres.' }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginForm() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: LoginFormValues) => api.post('/api/v1/auth/login', data),
    onSuccess: (data) => {
      localStorage.setItem('finehero_token', data.data.token);
      superheroToast.success('Login efetuado com sucesso!');
      router.push('/dashboard');
    },
    onError: (error: any) => {
      superheroToast.error(error.response?.data?.message || 'Ocorreu um erro ao fazer login.');
    },
  });

  const onSubmit = (data: LoginFormValues) => {
    mutation.mutate(data);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Entrar na sua conta</CardTitle>
        <CardDescription>Bem-vindo de volta! O FineHero está pronto para ajudar.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
            Entrar
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
