import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Extracao from './features/extracao/Extracao'
import TempoReal from './features/tempo-real/TempoReal'
import Configuracoes from './features/configuracoes/Configuracoes'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Extracao />} />
          <Route path="tempo-real" element={<TempoReal />} />
          <Route path="configuracoes" element={<Configuracoes />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
