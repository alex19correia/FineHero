export default function HowItWorksSection() {
  return (
    <section id="como-funciona" className="bg-white py-16">
      <div className="container mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold text-gray-800">Como funciona</h2>
        <div className="mt-8 grid gap-8 md:grid-cols-3">
          <div className="rounded-lg bg-gray-50 p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">1. Envia os dados da multa</h3>
            <p className="mt-4 text-gray-600">
              Tipo, data, local, descrição. Quanto mais detalhes, melhor a defesa.
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">
              2. O nosso motor RAG encontra a lei
            </h3>
            <p className="mt-4 text-gray-600">
              Analisamos a legislação e encontramos o modelo ideal para o seu caso.
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">3. Recebe PDF pronto com texto</h3>
            <p className="mt-4 text-gray-600">
              Carta pronta a enviar, com instruções claras para submeter a sua defesa.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
