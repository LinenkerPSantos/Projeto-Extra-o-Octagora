import { Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import api from '../../api/client'
import { useRegion } from '../../context/RegionContext'

const STATUS_LABEL = {
  idle: 'Aguardando',
  running: 'Executando',
  success: 'Concluído',
  error: 'Erro',
}

function fmtDatetime(iso) {
  return iso ? new Date(iso).toLocaleString('pt-BR') : '—'
}

export default function Dashboard() {
  const { regiao } = useRegion()

  const { data: downloadsData } = useQuery(
    ['downloads', regiao],
    () => api.get(`/downloads/${regiao}`).then(r => r.data)
  )
  const files = downloadsData?.files || []

  const { data: jobsData } = useQuery('jobs-status', () => api.get('/jobs/status').then(r => r.data), {
    refetchInterval: 5000,
  })
  const scripts = jobsData?.scripts || {}

  const jobsDaRegiao = Object.entries(scripts)
    .filter(([key]) => key.startsWith(`${regiao}:`))
    .map(([key, st]) => ({ script: key.split(':')[1], ...st }))
    .filter(j => j.started_at)
    .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))

  const tiles = [
    { label: 'Arquivos baixados', value: files.length, color: 'bg-gray-50 text-gray-700' },
    { label: 'Concluídos com sucesso', value: jobsDaRegiao.filter(j => j.status === 'success').length, color: 'bg-green-50 text-green-700' },
    { label: 'Com erro', value: jobsDaRegiao.filter(j => j.status === 'error').length, color: 'bg-red-50 text-red-700' },
    { label: 'Em execução agora', value: jobsDaRegiao.filter(j => j.status === 'running').length, color: 'bg-yellow-50 text-yellow-700' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Resumo do ambiente ativo — Agências {regiao}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {tiles.map(t => (
          <div key={t.label} className={`card p-4 ${t.color}`}>
            <div className="text-xs font-medium text-gray-500">{t.label}</div>
            <div className="text-2xl font-bold mt-1">{t.value}</div>
          </div>
        ))}
      </div>

      <Link to="/octagora" className="card p-5 hover:shadow-md transition-shadow block">
        <h2 className="font-semibold text-gray-800">📥 Extração Octagora</h2>
        <p className="text-sm text-gray-500 mt-1">Rodar relatórios e consolidar bases de {regiao}.</p>
      </Link>

      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Últimas execuções — {regiao}</h2>
        </div>
        {jobsDaRegiao.length === 0 ? (
          <p className="px-5 py-4 text-sm text-gray-500">Nenhuma execução registrada ainda nesta sessão do servidor.</p>
        ) : (
          <div className="divide-y divide-gray-50">
            {jobsDaRegiao.slice(0, 8).map(j => (
              <div key={j.script} className="px-5 py-2.5 flex items-center justify-between gap-4">
                <span className="text-sm text-gray-700">{j.script}</span>
                <span className={`badge-${j.status}`}>{STATUS_LABEL[j.status] || j.status}</span>
                <span className="text-xs text-gray-500">{fmtDatetime(j.started_at)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
