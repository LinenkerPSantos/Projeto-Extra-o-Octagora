import { createContext, useContext, useState } from 'react'

const RegionContext = createContext(null)

const STORAGE_KEY = 'octagora.regiao'

function loadInitial() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved === 'SP' || saved === 'ES' ? saved : 'ES'
  } catch {
    return 'ES'
  }
}

export function RegionProvider({ children }) {
  const [regiao, setRegiaoState] = useState(loadInitial)

  function setRegiao(value) {
    setRegiaoState(value)
    try {
      localStorage.setItem(STORAGE_KEY, value)
    } catch {
      // localStorage indisponível (modo privado etc.) — segue só em memória
    }
  }

  return (
    <RegionContext.Provider value={{ regiao, setRegiao }}>
      {children}
    </RegionContext.Provider>
  )
}

export function useRegion() {
  const ctx = useContext(RegionContext)
  if (!ctx) throw new Error('useRegion precisa estar dentro de <RegionProvider>')
  return ctx
}
