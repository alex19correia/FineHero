import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-gray-800 text-white">
      <div className="container mx-auto px-6 py-8">
        <div className="flex flex-col items-center justify-between sm:flex-row">
          <Link href="/" className="text-xl font-bold text-white hover:text-gray-200">
            FineHero
          </Link>
          <p className="mt-4 text-sm text-gray-400 sm:mt-0">
            &copy; {new Date().getFullYear()} FineHero. Todos os direitos reservados.
          </p>
          <div className="-mx-2 mt-4 flex sm:mt-0">
            <Link
              href="/politica-de-privacidade"
              className="mx-2 text-sm text-gray-400 hover:text-gray-200"
            >
              Política de privacidade
            </Link>
            <Link href="/termos-de-uso" className="mx-2 text-sm text-gray-400 hover:text-gray-200">
              Termos de uso
            </Link>
            <Link href="/contacto" className="mx-2 text-sm text-gray-400 hover:text-gray-200">
              Contacto
            </Link>
          </div>
        </div>
        <div className="mt-8 border-t border-gray-700 pt-8 text-center text-sm text-gray-400">
          <p>
            Disclaimer: &quot;Serviço automatizado. Nós não garantimos resultados; oferecemos
            geração de documentos.&quot;
          </p>
        </div>
      </div>
    </footer>
  );
}
