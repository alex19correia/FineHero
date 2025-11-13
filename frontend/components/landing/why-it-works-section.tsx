export default function WhyItWorksSection() {
  return (
    <section className="bg-gray-50 py-16">
      <div className="container mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold text-gray-800">Porquê funciona</h2>
        <div className="mt-8 grid gap-8 md:grid-cols-3">
          <div className="rounded-lg bg-white p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">Tecnologia RAG + Prompts</h3>
            <p className="mt-4 text-gray-600">
              Usamos a tecnologia mais avançada para encontrar a lei aplicável ao seu caso.
            </p>
          </div>
          <div className="rounded-lg bg-white p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">Economiza tempo e dinheiro</h3>
            <p className="mt-4 text-gray-600">
              Advogados cobrariam ~€100+. Connosco, a partir de €7,90, tem a sua defesa.
            </p>
          </div>
          <div className="rounded-lg bg-white p-8 shadow-md">
            <h3 className="text-xl font-bold text-gray-800">Opção de revisão humana</h3>
            <p className="mt-4 text-gray-600">
              Para casos mais complexos, pode solicitar a revisão por um advogado.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
