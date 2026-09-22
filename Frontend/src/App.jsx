import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { RegionProvider } from './context/RegionContext'
import Layout from './components/layout/Layout'
import Dashboard from './features/dashboard/Dashboard'
import Extracao from './features/extracao/Extracao'
import TempoReal from './features/tempo-real/TempoReal'
import Configuracoes from './features/configuracoes/Configuracoes'
import EmConstrucao from './features/em-construcao/EmConstrucao'

// Rotas fora do escopo de extração Octagora (mantidas só para o menu ficar
// visualmente igual ao Planejamento_Online) apontam para a mesma página
// "Em construção", cada uma com seu próprio título.
const PLACEHOLDERS = [
  { path: 'intradiario',            titulo: 'Intradiário'            },
  { path: 'atualizar-banco',        titulo: 'Atualizar Banco'        },
  { path: 'dimensionamento',        titulo: 'Dimensionamento'        },
  { path: 'cadop',                  titulo: 'CADOP'                  },
  { path: 'planejamento-ferias',    titulo: 'Planejamento Férias'    },
  { path: 'edp-online',             titulo: 'EDP Online'             },
  { path: 'monitoria',              titulo: 'Monitoria'              },
  { path: 'ouvidorias-reclamacoes', titulo: 'Ouvidorias/Reclamações' },
  { path: 'inconsistencia',         titulo: 'Inconsistência'         },
  { path: 'conferencia-ponto',      titulo: 'Conferência de Ponto'   },
]

export default function App() {
  return (
    <RegionProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="octagora" element={<Extracao />} />
            <Route path="tempo-real" element={<TempoReal />} />
            <Route path="configuracoes" element={<Configuracoes />} />
            {PLACEHOLDERS.map(p => (
              <Route key={p.path} path={p.path} element={<EmConstrucao titulo={p.titulo} />} />
            ))}
          </Route>
        </Routes>
      </BrowserRouter>
    </RegionProvider>
  )
}
