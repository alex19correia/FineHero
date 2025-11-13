import UploadZone from '@/components/upload/upload-zone';
import Image from 'next/image';

export default function UploadPage() {
  return (
    <div className="container mx-auto px-6 py-16 text-center">
      <h1 className="text-3xl font-bold text-gray-800 md:text-4xl">
        Vamos salvar-te desta multa!
      </h1>
      <p className="mt-6 text-gray-600">
        O FineHero está aqui para te ajudar. Carrega o documento da tua multa e nós tratamos do
        resto.
      </p>
      <div className="mt-12 flex flex-col items-center justify-center gap-8 md:flex-row">
        <Image
          src="/images/superhero/finehero-character.png"
          alt="FineHero Superhero"
          width={200}
          height={200}
        />
        <div className="w-full max-w-lg">
          <UploadZone />
        </div>
      </div>
    </div>
  );
}
