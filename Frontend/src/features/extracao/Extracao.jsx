import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import api from '../../api/client'
import { useRegion } from '../../context/RegionContext'

const STATUS_LABEL = {
  idle: 'Aguardando',
  running: 'Executando',
  success: 'Concluído',
  error: 'Erro',
}

const REPORTS = [
  { key: 'tempoprotocolo-sumario', label: 'Sumário',            regioes: ['ES', 'SP'] },
  { key: 'tempoprotocolo-detalhe', label: 'Detalhe',            regioes: ['ES', 'SP'] },
  { key: 'evento-usuario',         label: 'Evento do Usuário',  regioes: ['ES', 'SP'] },
  { key: 'nps-agencias',           label: 'NPS Agências',       regioes: ['SP'] },
  { key: 'nps-especializado',      label: 'NPS Especializado',  regioes: ['SP'] },
  { key: 'nps-video',              label: 'NPS Vídeo/Totem',    regioes: ['SP'] },
]
// Tempo Real (SLA) tem página própria — ver features/tempo-real/TempoReal.jsx

function yesterday() {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().slice(0, 10)
}

function toApiDate(yyyymmdd) {
  const [y, m, d] = yyyymmdd.split('-')
  return `${d}/${m}/${y}`
}

function fmtDatetime(iso) {
  return iso ? new Date(iso).toLocaleString('pt-BR') : '—'
}

function fmtSize(kb) {
  return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`
}

function downloadBlob(data, filename) {
  const url = window.URL.createObjectURL(new Blob([data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function ReportRow({ item, st, onExtract, disabled }) {
  const isRunning = st.status === 'running'
  return (
    <div className="px-5 py-3 flex items-center justify-between gap-4">
      <span className="text-sm font-medium text-gray-700 w-48">{item.label}</span>
      <span className={`badge-${st.status}`}>{STATUS_LABEL[st.status] || st.status}</span>
      <span className="text-xs text-gray-500 flex-1">
        Início: {fmtDatetime(st.started_at)} · Fim: {fmtDatetime(st.finished_at)}
      </span>
      <button className="btn-secondary btn-sm" onClick={onExtract} disabled={disabled}>
        {isRunning ? 'Executando...' : 'Extrair'}
      </button>
    </div>
  )
}

export default function Extracao() {
  const { regiao } = useRegion()
  const [dateStart, setDateStart] = useState(yesterday())
  const [dateEnd, setDateEnd] = useState(yesterday())
  const [consolidating, setConsolidating] = useState(false)
  const [consolidatingGeral, setConsolidatingGeral] = useState(false)
  const logBoxRef = useRef(null)
  const queryClient = useQueryClient()

  const { data } = useQuery('jobs-status', () => api.get('/jobs/status').then(r => r.data), {
    refetchInterval: 2000,
  })

  const scripts = data?.scripts || {}
  const logs = data?.logs || []
  const anyRunning = Object.values(scripts).some(s => s.status === 'running')
  const rangeInvalid = dateStart && dateEnd && dateStart > dateEnd

  const { data: downloadsData } = useQuery(
    ['downloads', regiao],
    () => api.get(`/downloads/${regiao}`).then(r => r.data),
    { refetchInterval: anyRunning ? 3000 : 10000 }
  )
  const files = downloadsData?.files || []

  useEffect(() => {
    if (logBoxRef.current) logBoxRef.current.scrollTop = logBoxRef.current.scrollHeight
  }, [logs])

  async function startRange(scriptKey) {
    try {
      await api.post(`/jobs/start-range/${regiao}/${scriptKey}`, {
        date_start: toApiDate(dateStart),
        date_end: toApiDate(dateEnd),
      })
      queryClient.invalidateQueries('jobs-status')
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao iniciar a extração.')
    }
  }

  async function clearLogs() {
    await api.delete('/jobs/logs')
    queryClient.invalidateQueries('jobs-status')
  }

  async function deleteFile(name) {
    if (!window.confirm(`Excluir o arquivo "${name}"?`)) return
    try {
      await api.delete(`/downloads/${regiao}/${encodeURIComponent(name)}`)
      queryClient.invalidateQueries(['downloads', regiao])
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao excluir o arquivo.')
    }
  }

  async function downloadConsolidado() {
    setConsolidating(true)
    try {
      const res = await api.get(`/downloads/${regiao}/consolidado`, { responseType: 'blob' })
      downloadBlob(res.data, `Consolidado_${regiao}.xls`)
    } catch (err) {
      let message = 'Erro ao gerar o arquivo consolidado.'
      if (err.response?.data instanceof Blob) {
        try {
          const parsed = JSON.parse(await err.response.data.text())
          message = parsed.detail || message
        } catch {}
      }
      alert(message)
    } finally {
      setConsolidating(false)
    }
  }

  async function downloadConsolidadoGeral() {
    setConsolidatingGeral(true)
    try {
      const res = await api.get('/downloads/consolidado-geral', { responseType: 'blob' })
      downloadBlob(res.data, 'Consolidado_Geral_SP_ES.xls')
    } catch (err) {
      let message = 'Erro ao gerar o arquivo consolidado geral.'
      if (err.response?.data instanceof Blob) {
        try {
          const parsed = JSON.parse(await err.response.data.text())
          message = parsed.detail || message
        } catch {}
      }
      alert(message)
    } finally {
      setConsolidatingGeral(false)
    }
  }

  async function clearAllFiles() {
    if (!window.confirm(`Excluir todos os arquivos da pasta de downloads (${regiao})?`)) return
    try {
      await api.delete(`/downloads/${regiao}`)
      queryClient.invalidateQueries(['downloads', regiao])
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao limpar os arquivos.')
    }
  }

  function getStatus(key) {
    return scripts[`${regiao}:${key}`] || { status: 'idle', started_at: null, finished_at: null }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Octagora — Extração Consolidada</h1>
          <p className="text-gray-500 text-sm mt-1">
            Extração de relatórios por intervalo de datas — ambiente ativo: <strong>{regiao}</strong>
            {' '}(troque no seletor do cabeçalho)
          </p>
        </div>
        <button
          className="btn-secondary"
          onClick={downloadConsolidadoGeral}
          disabled={consolidatingGeral}
          title="Junta os arquivos de SP e ES em um único consolidado, com a coluna Regiao"
        >
          {consolidatingGeral ? 'Consolidando...' : 'Consolidado Geral (SP + ES)'}
        </button>
      </div>

      {/* Intervalo de datas */}
      <div className="card p-5">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Data Inicial</label>
            <input
              type="date"
              className="input"
              value={dateStart}
              onChange={e => setDateStart(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Data Final</label>
            <input
              type="date"
              className="input"
              value={dateEnd}
              onChange={e => setDateEnd(e.target.value)}
            />
          </div>
          <div className="flex-1 text-sm text-gray-500">
            {rangeInvalid
              ? <span className="text-red-600">Data inicial deve ser anterior ou igual à data final.</span>
              : `Extrai Sumário e Detalhe dia a dia (${regiao}), da data inicial até a data final.`}
          </div>
          <button
            className="btn-primary"
            onClick={() => startRange('extrair-tudo')}
            disabled={anyRunning || rangeInvalid}
          >
            {getStatus('extrair-tudo').status === 'running' ? 'Executando...' : 'Extrair Tudo'}
          </button>
          <button
            className="btn-secondary"
            onClick={downloadConsolidado}
            disabled={consolidating}
            title={`Junta todos os sumarioDDMMAAAA.csv e detalheDDMMAAAA.csv de ${regiao} em um único arquivo, com a coluna MesBase`}
          >
            {consolidating ? 'Consolidando...' : `Consolidar ${regiao}`}
          </button>
        </div>
      </div>

      {/* Relatórios individuais */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Relatórios — {regiao}</h2>
        </div>
        <div className="divide-y divide-gray-50">
          {REPORTS.filter(item => item.regioes.includes(regiao)).map(item => (
            <ReportRow
              key={item.key}
              item={item}
              st={getStatus(item.key)}
              onExtract={() => startRange(item.key)}
              disabled={anyRunning || rangeInvalid}
            />
          ))}
        </div>
      </div>

      {/* Arquivos baixados */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Arquivos em downloads/{regiao}/</h2>
          <button className="btn-danger btn-sm" onClick={clearAllFiles} disabled={files.length === 0}>
            Limpar Tudo
          </button>
        </div>
        {files.length === 0 ? (
          <p className="px-5 py-4 text-sm text-gray-500">Nenhum arquivo encontrado.</p>
        ) : (
          <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto">
            {files.map(f => (
              <div key={f.name} className="px-5 py-2.5 flex items-center justify-between gap-4">
                <span className="text-sm font-mono text-gray-700 truncate">{f.name}</span>
                <div className="flex items-center gap-3 text-xs text-gray-500 shrink-0">
                  <span className="badge-idle">{f.type}</span>
                  {f.date && <span>📅 {f.date}</span>}
                  <span>{fmtSize(f.size_kb)}</span>
                  <a
                    className="btn-secondary btn-sm"
                    href={`/api/downloads/${regiao}/${encodeURIComponent(f.name)}/download`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Baixar
                  </a>
                  <button className="btn-danger btn-sm" onClick={() => deleteFile(f.name)}>
                    Excluir
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Log de execução */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Log de Execução</h2>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">{logs.length} linha{logs.length !== 1 ? 's' : ''}</span>
            <button className="btn-secondary btn-sm" onClick={clearLogs} disabled={logs.length === 0}>
              Limpar
            </button>
          </div>
        </div>
        <pre
          ref={logBoxRef}
          className="bg-gray-900 text-gray-200 m-0 p-4 rounded-b-xl text-xs font-mono overflow-y-auto whitespace-pre-wrap break-words"
          style={{ maxHeight: '360px', minHeight: '80px' }}
        >
          {logs.length === 0
            ? <span className="text-gray-500">Nenhum log disponível. Selecione uma região, um intervalo e clique em "Extrair Tudo".</span>
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
