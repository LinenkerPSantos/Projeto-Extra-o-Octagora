export default function EmConstrucao({ titulo }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{titulo}</h1>
        <p className="text-gray-500 text-sm mt-1">Este módulo não faz parte do escopo de extração Octagora.</p>
      </div>

      <div className="card p-10 flex flex-col items-center justify-center text-center gap-2">
        <span className="text-4xl">🚧</span>
        <p className="text-gray-600 font-medium">Em construção</p>
        <p className="text-sm text-gray-400 max-w-sm">
          Este projeto cobre só extração e consolidação do Octagora (SP + ES).
          Este item existe aqui apenas para manter o menu igual ao Planejamento_Online.
        </p>
      </div>
    </div>
  )
}
