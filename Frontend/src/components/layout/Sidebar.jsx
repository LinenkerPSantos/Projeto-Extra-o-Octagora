import { NavLink } from 'react-router-dom'

// Ferramenta de script local, sem login/perfis — por isso o menu é uma lista
// fixa, sem o accordion por grupo/permissão do Planejamento_Online.
const NAV_ITEMS = [
  { to: '/',              label: 'Extração',        icon: '📥', end: true },
  { to: '/tempo-real',    label: 'Tempo Real (SLA)', icon: '⏱️' },
  { to: '/configuracoes', label: 'Configurações',   icon: '⚙️' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-primary-900 text-white flex flex-col shrink-0 overflow-hidden">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-primary-700">
        <div className="text-xs font-bold text-white uppercase tracking-wide leading-tight">
          Octagora
        </div>
        <div className="text-xs text-primary-300 leading-tight mt-0.5">
          Extração Consolidada — SP + ES
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 text-sm transition-colors border-b border-primary-800 ${
                isActive
                  ? 'bg-primary-700 text-white font-medium'
                  : 'text-primary-200 hover:bg-primary-800 hover:text-white'
              }`
            }
          >
            <span className="text-base leading-none">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Rodapé — sem login, então sem botão "Sair" */}
      <div className="px-4 py-3 border-t border-primary-700 text-xs text-primary-400">
        Execução 100% local
      </div>
    </aside>
  )
}
