import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import api from '../../api/client'

const REGIOES = [
  { key: 'ES', label: 'Agências - ES' },
  { key: 'SP', label: 'Agências - SP' },
]

function CredentialCard({ regiao, label, saved }) {
  const [user, setUser] = useState('')
  const [password, setPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [savedMsg, setSavedMsg] = useState('')
  const queryClient = useQueryClient()

  useEffect(() => {
    setUser(saved?.user || '')
  }, [saved?.user])

  async function handleSave(e) {
    e.preventDefault()
    if (!user.trim() && !password.trim()) {
      alert('Informe usuário e/ou senha para salvar.')
      return
    }
    setSaving(true)
    setSavedMsg('')
    try {
      await api.put(`/settings/credentials/${regiao}`, {
        user: user.trim() || undefined,
        password: password.trim() || undefined,
      })
      setPassword('')
      setSavedMsg('Salvo.')
      queryClient.invalidateQueries('credentials')
      setTimeout(() => setSavedMsg(''), 2500)
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao salvar as credenciais.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="card p-5 space-y-4" onSubmit={handleSave}>
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-800">{label}</h2>
        <span className={saved?.has_password ? 'badge-success' : 'badge-error'}>
          {saved?.has_password ? 'Senha cadastrada' : 'Senha não cadastrada'}
        </span>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Usuário (login)</label>
        <input
          type="text"
          className="input"
          value={user}
          onChange={e => setUser(e.target.value)}
          autoComplete="off"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Senha</label>
        <input
          type="password"
          className="input"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder={saved?.has_password ? '•••••••• (deixe em branco para manter)' : 'Digite a senha'}
          autoComplete="new-password"
        />
      </div>

      <div className="flex items-center gap-3">
        <button type="submit" className="btn-primary btn-sm" disabled={saving}>
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
        {savedMsg && <span className="text-sm text-emerald-600">{savedMsg}</span>}
      </div>
    </form>
  )
}

export default function Configuracoes() {
  const { data } = useQuery('credentials', () => api.get('/settings/credentials').then(r => r.data))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
        <p className="text-gray-500 text-sm mt-1">
          Cadastre o usuário e a senha do Octagora para cada região. Ficam salvos no servidor
          (Backend/credentials.json) — não precisa editar arquivo nenhum nem reiniciar o Backend.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {REGIOES.map(r => (
          <CredentialCard key={r.key} regiao={r.key} label={r.label} saved={data?.[r.key]} />
        ))}
      </div>
    </div>
  )
}
