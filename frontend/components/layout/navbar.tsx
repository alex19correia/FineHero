'use client';

import Link from 'next/link';
import Button from '../ui/button';
import { useAuth } from '@/hooks/use-auth';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 bg-white shadow-md">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold text-gray-700">
            <Link href="/" className="text-gray-800 hover:text-gray-700">
              FineHero
            </Link>
          </div>
          <div className="hidden md:flex md:items-center">
            <Link href="/#como-funciona" className="mx-3 text-gray-600 hover:text-gray-800">
              Como Funciona
            </Link>
            <Link href="/#precos" className="mx-3 text-gray-600 hover:text-gray-800">
              Preços
            </Link>
            {user ? (
              <>
                <Link href="/dashboard" className="mx-3 text-gray-600 hover:text-gray-800">
                  Dashboard
                </Link>
                <Button onClick={logout} size="sm" variant="secondary">
                  Sair
                </Button>
              </>
            ) : (
              <>
                <Link href="/login" className="mx-3 text-gray-600 hover:text-gray-800">
                  Entrar
                </Link>
                <Link href="/register">
                  <Button size="sm">Registar</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
