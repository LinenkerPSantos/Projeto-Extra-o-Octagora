import { useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import api from '../../api/client'
import { useRegion } from '../../context/RegionContext'

const RISCO_STYLE = {
  'CRÍTICO':    'bg-red-100 text-red-700',
  'ALTO RISCO': 'bg-orange-100 text-orange-700',
  'ATENÇÃO':    'bg-yellow-100 text-yellow-700',
  'NORMAL':     'bg-green-100 text-green-700',
}

// Classes completas e literais (não interpoladas) — o Tailwind só gera no
// build o CSS de classes que aparecem escritas por extenso no código-fonte.
const TOTAL_TILES = [
  { key: 'total',             label: 'Total na fila',     tile: 'bg-gray-50 border-gray-100',     text: 'text-gray-700'   },
  { key: 'critico',           label: 'Críticos',          tile: 'bg-red-50 border-red-100',       text: 'text-red-700'    },
  { key: 'alto_risco',        label: 'Alto Risco',        tile: 'bg-orange-50 border-orange-100', text: 'text-orange-700' },
  { key: 'atencao',           label: 'Atenção',           tile: 'bg-yellow-50 border-yellow-100', text: 'text-yellow-700' },
  { key: 'normal',            label: 'Normal',            tile: 'bg-green-50 border-green-100',   text: 'text-green-700'  },
  { key: 'atrasados',         label: 'Atrasados (SLA)',   tile: 'bg-red-50 border-red-100',       text: 'text-red-700'    },
  { key: 'agencias_em_risco', label: 'Agências em risco', tile: 'bg-orange-50 border-orange-100', text: 'text-orange-700' },
]

function RiscoBadge({ risco }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${RISCO_STYLE[risco] || 'bg-gray-100 text-gray-600'}`}>
      {risco}
    </span>
  )
}

export default function TempoReal() {
  const { regiao } = useRegion()
  const logBoxRef = useRef(null)
  const queryClient = useQueryClient()

  const { data: jobsData } = useQuery('jobs-status', () => api.get('/jobs/status').then(r => r.data), {
    refetchInterval: 2000,
  })
  const scripts = jobsData?.scripts || {}
  const logs = jobsData?.logs || []
  const jobKey = `${regiao}:tempo-real`
  const status = scripts[jobKey]?.status || 'idle'
  const isRunning = status === 'running'

  const { data, isError, refetch } = useQuery(
    ['tempo-real', regiao],
    () => api.get(`/downloads/${regiao}/tempo_real.json/download`).then(r => r.data),
    { retry: false, refetchOnWindowFocus: false }
  )

  // Assim que o job termina, busca o JSON recém-gerado.
  useEffect(() => {
    if (status === 'success') refetch()
  }, [status, refetch])

  useEffect(() => {
    if (logBoxRef.current) logBoxRef.current.scrollTop = logBoxRef.current.scrollHeight
  }, [logs])

  async function coletarAgora() {
    try {
      await api.post(`/jobs/start-range/${regiao}/tempo-real`, {})
      queryClient.invalidateQueries('jobs-status')
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao iniciar a coleta.')
    }
  }

  const totais = data?.totais
  const agencias = data?.agencias || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tempo Real (SLA)</h1>
        <p className="text-gray-500 text-sm mt-1">
          Fila do Dashboard Presencial no momento da coleta — ambiente ativo: <strong>{regiao}</strong>
          {' '}(troque no seletor do cabeçalho)
        </p>
      </div>

      {/* Ação + status da última coleta */}
      <div className="card p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="text-sm text-gray-500">
          {data?.timestamp
            ? <>Última coleta ({regiao}): <span className="font-medium text-gray-700">{data.timestamp}</span></>
            : isError
              ? 'Nenhuma coleta encontrada ainda para esta região.'
              : 'Carregando...'}
        </div>
        <button className="btn-primary" onClick={coletarAgora} disabled={isRunning}>
          {isRunning ? 'Coletando...' : 'Coletar Agora'}
        </button>
      </div>

      {/* Totais */}
      {totais && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {TOTAL_TILES.map(tile => (
            <div key={tile.key} className={`card p-4 ${tile.tile}`}>
              <div className="text-xs font-medium text-gray-500">{tile.label}</div>
              <div className={`text-2xl font-bold mt-1 ${tile.text}`}>{totais[tile.key] ?? 0}</div>
            </div>
          ))}
        </div>
      )}

      {/* Ranking por agência */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Agências — {regiao}</h2>
        </div>
        {agencias.length === 0 ? (
          <p className="px-5 py-4 text-sm text-gray-500">Nenhum dado coletado ainda. Clique em "Coletar Agora".</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs font-medium text-gray-500 border-b border-gray-100">
                  <th className="px-5 py-2">Agência</th>
                  <th className="px-3 py-2">Risco</th>
                  <th className="px-3 py-2">Tickets</th>
                  <th className="px-3 py-2">Espera Máx</th>
                  <th className="px-3 py-2">Espera Média</th>
                  <th className="px-3 py-2">Atrasado</th>
                  <th className="px-3 py-2">Alerta</th>
                  <th className="px-3 py-2">OK</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {agencias.map(a => (
                  <tr key={a.agencia}>
                    <td className="px-5 py-2.5 font-medium text-gray-700">{a.agencia}</td>
                    <td className="px-3 py-2.5"><RiscoBadge risco={a.risco} /></td>
                    <td className="px-3 py-2.5">{a.tickets}</td>
                    <td className="px-3 py-2.5 font-mono">{a.espera_max}</td>
                    <td className="px-3 py-2.5 font-mono">{a.espera_med}</td>
                    <td className="px-3 py-2.5">{a.atrasado}</td>
                    <td className="px-3 py-2.5">{a.alerta}</td>
                    <td className="px-3 py-2.5">{a.ok}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Log de execução */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Log de Execução</h2>
        </div>
        <pre
          ref={logBoxRef}
          className="bg-gray-900 text-gray-200 m-0 p-4 rounded-b-xl text-xs font-mono overflow-y-auto whitespace-pre-wrap break-words"
          style={{ maxHeight: '280px', minHeight: '80px' }}
        >
          {logs.length === 0
            ? <span className="text-gray-500">Nenhum log disponível.</span>
            : logs.map((line, i) => {
                const color =
                  line.includes('[STDERR]') || line.includes('Traceback') || line.includes('Error:') ? 'text-red-400' :
                  line.includes('[ERRO]') || line.includes('✗') ? 'text-red-300' :
                  line.includes('[AVISO]') ? 'text-yellow-300' :
                  line.includes('✓') ? 'text-emerald-300' :
                  line.startsWith('─') || line.startsWith('═') || line.startsWith('-') ? 'text-gray-500' : ''
                return <span key={i} className={color}>{line + '\n'}</span>
              })
          }
        </pre>
      </div>
    </div>
  )
}
