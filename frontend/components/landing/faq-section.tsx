export default function FaqSection() {
  return (
    <section className="bg-gray-50 py-16">
      <div className="container mx-auto px-6">
        <h2 className="text-center text-3xl font-bold text-gray-800">
          Perguntas Frequentes
        </h2>
        <div className="mx-auto mt-8 max-w-3xl">
          <div className="rounded-lg bg-white p-6 shadow-md">
            <h3 className="text-lg font-bold text-gray-800">É aconselhamento jurídico?</h3>
            <p className="mt-2 text-gray-600">
              Fornecemos um documento automatizado baseado em legislação — não substitui
              aconselhamento jurídico. Para representação legal, oferecemos revisão paga por
              advogado.
            </p>
          </div>
          <div className="mt-4 rounded-lg bg-white p-6 shadow-md">
            <h3 className="text-lg font-bold text-gray-800">Será aceite o recurso gerado?</h3>
            <p className="mt-2 text-gray-600">
              A carta segue formatos legais e cita artigos; a aceitação depende da autoridade que
              analisa cada caso. Em casos complexos recomendamos a revisão humana.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
