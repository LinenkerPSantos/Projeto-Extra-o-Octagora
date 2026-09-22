import { useState } from 'react'
import { NavLink } from 'react-router-dom'

// Mesma estrutura de grupos do Planejamento_Online — sem filtro por perfil
// (não há login/roles aqui). Itens fora do escopo de extração Octagora
// (Dashboard além do resumo, Qualidade, RH, etc.) apontam para uma página
// "Em construção", só para manter o menu visualmente completo.
const SECTIONS = [
  {
    group: 'Dashboard',
    icon: '🏠',
    items: [
      { to: '/',            label: 'Dashboard',   end: true },
      { to: '/intradiario', label: 'Intradiário' },
    ],
  },
  {
    group: 'Planejamento',
    icon: '📊',
    items: [
      { to: '/octagora',            label: 'Octagora'            },
      { to: '/atualizar-banco',     label: 'Atualizar Banco'     },
      { to: '/dimensionamento',     label: 'Dimensionamento'     },
      { to: '/cadop',               label: 'CADOP'               },
      { to: '/planejamento-ferias', label: 'Planejamento Férias' },
    ],
  },
  {
    group: 'Qualidade',
    icon: '🎧',
    items: [
      { to: '/edp-online',              label: 'EDP Online'             },
      { to: '/monitoria',               label: 'Monitoria'              },
      { to: '/ouvidorias-reclamacoes',  label: 'Ouvidorias/Reclamações' },
      { to: '/inconsistencia',          label: 'Inconsistência'         },
    ],
  },
  {
    group: 'RH',
    icon: '⏱️',
    items: [
      { to: '/conferencia-ponto', label: 'Conferência de Ponto' },
    ],
  },
  {
    group: 'Administrador',
    icon: '👥',
    items: [
      { to: '/configuracoes', label: 'Configurações' },
    ],
  },
]

export default function Sidebar() {
  const [open, setOpen] = useState(
    Object.fromEntries(SECTIONS.map((_, i) => [i, true]))
  )

  function toggle(idx) {
    setOpen(prev => ({ ...prev, [idx]: !prev[idx] }))
  }

  return (
    <aside className="w-56 bg-primary-900 text-white flex flex-col shrink-0 overflow-hidden">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-primary-700">
        <div className="text-xs font-bold text-white uppercase tracking-wide leading-tight">
          SGPP
        </div>
        <div className="text-xs text-primary-300 leading-tight mt-0.5">
          Extração Octagora — SP + ES
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto">
        {SECTIONS.map((section, idx) => {
          const isOpen = open[idx]
          return (
            <div key={idx}>
              <button
                onClick={() => toggle(idx)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-primary-800 transition-colors border-b border-primary-700"
              >
                <div className="flex items-center gap-2">
                  <span className="text-base leading-none">{section.icon}</span>
                  <span className="text-xs font-bold uppercase tracking-wider text-white">
                    {section.group}
                  </span>
                </div>
                <span className={`text-primary-300 text-xs transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}>
                  ▶
                </span>
              </button>

              <div
                style={{ maxHeight: isOpen ? '400px' : '0px' }}
                className="overflow-hidden transition-all duration-200 bg-primary-950"
              >
                {section.items.map(item => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-5 py-2.5 text-sm transition-colors border-b border-primary-800 ${
                        isActive
                          ? 'bg-primary-700 text-white font-medium'
                          : 'text-primary-200 hover:bg-primary-800 hover:text-white'
                      }`
                    }
                  >
                    <span className="text-primary-400 text-xs">○</span>
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          )
        })}
      </nav>

      {/* Rodapé — sem login, então sem botão "Sair" */}
      <div className="px-4 py-3 border-t border-primary-700 text-xs text-primary-400">
        Execução 100% local
      </div>
    </aside>
  )
}
