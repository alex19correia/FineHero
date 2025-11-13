'use client';

import { useAuth } from '@/hooks/use-auth';
import Button from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const { data: fines, isLoading } = useQuery({
    queryKey: ['fines'],
    queryFn: () => api.get('/api/v1/fines').then((res) => res.data),
  });

  if (isLoading) {
    return <div>A carregar...</div>;
  }

  const stats = {
    total: fines?.length || 0,
    completed: fines?.filter((f: any) => f.status === 'completed').length || 0,
    pending: fines?.filter((f: any) => f.status !== 'completed').length || 0,
  };

  return (
    <div className="container mx-auto px-6 py-16">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          Dashboard - Olá {user?.full_name}! O FineHero está aqui para te ajudar.
        </h1>
        <Button onClick={logout} variant="secondary">
          Sair
        </Button>
      </div>
      <div className="mt-8 grid gap-8 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total de Multas</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Multas Resolvidas</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-green-500">{stats.completed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Multas Pendentes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-yellow-500">{stats.pending}</p>
          </CardContent>
        </Card>
      </div>
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">As Tuas Multas</h2>
          <Link href="/upload">
            <Button>Carregar Nova Multa</Button>
          </Link>
        </div>
        <div className="mt-4">
          {fines?.length > 0 ? (
            <div className="space-y-4">
              {fines.map((fine: any) => (
                <Link key={fine.id} href={`/fine/${fine.id}`}>
                  <Card className="cursor-pointer transition-shadow hover:shadow-md">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-bold">{fine.fine_type}</p>
                          <p className="text-sm text-gray-600">{fine.location}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold">€{fine.fine_amount}</p>
                          <p
                            className={`text-sm ${
                              fine.status === 'completed' ? 'text-green-500' : 'text-yellow-500'
                            }`}
                          >
                            {fine.status}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <div className="mt-8 text-center">
              <p className="text-gray-600">Ainda não tens multas. Carrega a tua primeira multa!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
