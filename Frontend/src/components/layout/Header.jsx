import { useQuery } from 'react-query'
import api from '../../api/client'
import { useRegion } from '../../context/RegionContext'

export default function Header() {
  const { regiao, setRegiao } = useRegion()

  const { data, isError } = useQuery(
    'health',
    () => api.get('/health').then(r => r.data),
    { refetchInterval: 15000, retry: 1 }
  )
  const online = !isError && data?.status === 'ok'

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
      <span className={online ? 'badge-success' : 'badge-error'}>
        {online ? '● Backend online' : '● Backend indisponível'}
      </span>

      {/* Ambiente ativo (SP/ES) — substitui o usuário logado, já que não há login */}
      <div className="flex items-center gap-3 text-sm text-gray-600">
        <span className="font-medium">Ambiente</span>
        <div className="flex rounded-lg border border-gray-300 overflow-hidden">
          {['ES', 'SP'].map(r => (
            <button
              key={r}
              onClick={() => setRegiao(r)}
              className={`px-3 py-1 text-xs font-semibold transition-colors ${
                regiao === r
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}
