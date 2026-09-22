import { useQuery } from 'react-query'
import api from '../../api/client'

export default function Header() {
  const { data, isError } = useQuery(
    'health',
    () => api.get('/health').then(r => r.data),
    { refetchInterval: 15000, retry: 1 }
  )
  const online = !isError && data?.status === 'ok'

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
      <div />
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span className={online ? 'badge-success' : 'badge-error'}>
          {online ? '● Backend online' : '● Backend indisponível'}
        </span>
      </div>
    </header>
  )
}
