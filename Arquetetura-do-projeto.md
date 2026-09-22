# Arquitetura do Projeto — Planejamento Extração Octagora

> Documento vivo. Cada fase tem um status que deve ser atualizado conforme o
> desenvolvimento avança. Perguntas em aberto ficam marcadas explicitamente —
> não adivinhar regra de negócio não definida, perguntar antes de implementar.

## 1. Visão geral

Hoje o projeto é uma ferramenta de extração e consolidação de relatórios do
Octagora (SP e ES), sem login e sem banco de dados — cada extração gera CSVs
locais que podem ser consolidados em Excel sob demanda.

A visão de longo prazo (este documento) é evoluir esse projeto, fase a fase,
até cobrir o mesmo escopo do `Planejamento_Online` (Octagora, Dimensionamento,
CADOP, Planejamento de Férias, Qualidade, RH), mas com uma arquitetura mais
simples: **sem login**, **SP e ES como ambientes totalmente separados**, e um
banco de dados local (SQLite) alimentado a partir da Fase 3 em diante.

## 2. Princípios de arquitetura

1. **Sem login/senha de usuário do sistema.** Não existe conceito de conta,
   perfil ou permissão. O único "login" que existe é o par usuário/senha do
   Octagora, cadastrado na aba Configurações (por região).
2. **SP e ES são ambientes separados**, não uma feature com um filtro de
   região. Cada um é tratado como se fosse "um programa próprio que
   compartilha o mesmo site" — sem consolidação cruzada entre os dois (o
   antigo "Consolidado Geral (SP + ES)" foi removido por causa disso).
3. **Menu igual ao `Planejamento_Online`** — os grupos e itens do menu lateral
   são os mesmos, mesmo que várias funcionalidades ainda não existam (ficam
   como "Em construção" até a fase correspondente ser implementada).
4. **Banco de dados só entra a partir da Fase 3.** Até lá, tudo continua
   baseado em arquivo (CSV/Excel). Quando o banco entrar, será **SQLite**,
   local, um arquivo por região (proposta: `edp_sp.db` e `edp_es.db` —
   ver pergunta em aberto na Fase 2).
5. **Toda extração continua sem gravar direto no banco.** O fluxo é sempre:
   extrai → gera arquivo → um passo separado importa o arquivo pro banco.
   Isso mantém o log de execução e os CSVs como fonte de verdade auditável.

## 3. Estado atual (já implementado)

| Item | Status |
|---|---|
| Backend FastAPI + Selenium para extração Octagora (SP/ES) | ✅ Feito |
| Relatórios: Sumário, Detalhe, Evento do Usuário | ✅ Feito (SP + ES) |
| Relatórios: NPS Agências, NPS Especializado, NPS Vídeo/Totem | ✅ Feito (só SP — não existem em ES) |
| Consolidação em Excel por região | ✅ Feito |
| ~~Consolidado Geral (SP + ES)~~ | ❌ Removido (Fase 1) |
| ~~Tempo Real (SLA)~~ | ❌ Removido (Fase 1 — não é mais necessário para este projeto) |
| Aba Configurações (usuário/senha Octagora por região) | ✅ Feito |
| Layout com sidebar em grupos (igual `Planejamento_Online`), sem login | ✅ Feito |
| Seletor global de ambiente (SP/ES) no cabeçalho | ✅ Feito |
| Dashboard com resumo do ambiente ativo | ✅ Feito (versão simples) |
| Itens de menu fora do escopo atual (Atualizar Banco, Dimensionamento, CADOP, Planejamento Férias, Qualidade, RH) | 🚧 Placeholder "Em construção" |
| Banco de dados | ⬜ Não iniciado (Fase 2/3) |

## 4. Estrutura de pastas/arquivos por região

```
Pastas de SP
  - Octagora
      - Sumário
      - Detalhado
      - Evento do Usuário
      - NPS Agências
      - NPS Especializado
      - NPS Vídeo/Totem

Pastas de ES
  - Octagora
      - Sumário
      - Detalhado
      - Evento do Usuário
      - NPS Agências  → pendente (fase exclusiva, ver pergunta 4.1)
```

> **4.1 Pergunta em aberto:** o NPS de ES é "pendente" porque o formulário
> ainda não existe no ambiente Octagora ES, ou porque existe mas o token/nome
> ainda não foi levantado? Isso muda se é uma tarefa de "descobrir o token"
> (rápida) ou "esperar a área criar o formulário" (fora do nosso controle).

A partir daqui (Fase 3 em diante), tudo passa a ser importado para o banco de
dados a partir de uma planilha de Excel:

- **Atualizar Banco** — lista as tabelas do banco (Octagora, Qualidade, RH)
  só para visualização.
- **Dimensionamento** — usa a tabela CADOP + a tabela Evento do Usuário para
  comparar e calcular necessidade de HC.
- **CADOP** — tabela-base que também alimenta outros projetos; tem um campo
  de manutenção de status.
- **Planejamento de Férias** — usa a tabela CADOP.

### Qualidade

Sempre com duas funcionalidades por módulo:
1. **Atualizar Banco Qualidade** — usuário sobe uma planilha Excel específica
   da função, que atualiza o banco.
2. **Dashboard Qualidade** — campos com os resultados extraídos.

Módulos: EDP Online, Monitoria, Ouvidorias e Reclamações (duas coisas
diferentes), Inconsistências (duas planilhas diferentes: *Alteração de
Titularidade* e *Notas Improcedentes*).

### RH

Totalmente pendente — terá uma fase exclusiva (ver Fase 6).

## 5. Fases

Cada fase abaixo tem: objetivo, escopo, entregáveis, critério de "pronto" e
perguntas em aberto. Status inicial de todas: **⬜ Não iniciado**, exceto
onde indicado.

---

### Fase 1 — Separação SP/ES e limpeza de escopo

**Status: ✅ Concluída**

**Objetivo:** consolidar a arquitetura atual antes de começar a mexer em
banco de dados.

**Escopo:**
- [x] SP e ES como ambientes separados, cada um com sua rota/estado — já
      existia via seletor global de região; cada endpoint do backend é
      escopado por região (`/api/.../{regiao}/...`).
- [x] Remover o "Consolidado Geral (SP + ES)" — cada região gera seu próprio
      consolidado, sem cruzar dados.
- [x] Remover a funcionalidade Tempo Real (SLA) — não é mais necessária.
- [ ] Levantamento dos requisitos para rodar o projeto localmente (ver
      seção 6 deste documento).
- [ ] Cronograma com base nas fases (ver seção 7).

---

### Fase 2 — Modelagem do banco de dados

**Objetivo:** desenhar as tabelas do banco, com EDP_SP e EDP_ES em ambientes
separados.

**Escopo proposto:**
- Um arquivo SQLite por região (`Backend/database/edp_sp.db` e
  `edp_es.db`), não um banco único com coluna de região — mantém o
  princípio "ambientes separados" também no nível de dados.
- Tabelas iniciais: espelhar os relatórios já extraídos (Sumário, Detalhe,
  Evento do Usuário, NPS x3) + CADOP.
- Definir chave primária/de deduplicação por tabela (o quê identifica uma
  linha como "a mesma" entre duas importações do mesmo dia?).

**Perguntas em aberto:**
- **5.2.1** Confirma um arquivo `.db` por região (proposta acima), ou prefere
  um banco único com coluna `regiao` (mais fácil pra relatório combinado no
  futuro, mas fere o princípio de ambientes 100% separados)?
- **5.2.2** As tabelas do banco devem manter as colunas exatamente como vêm
  do CSV do Octagora, ou já normalizar nomes de coluna (ex.: sem acento,
  snake_case)?
- **5.2.3** Qual o volume esperado (linhas/dia, quantos meses de histórico
  ficam no banco)? Isso decide se SQLite aguenta tranquilo ou se algum dia
  precisa migrar para Postgres.

---

### Fase 3 — Importação Octagora → banco + CADOP

**Objetivo:** trocar "Consolidar" (gera Excel) por "Subir para o banco"
(grava no SQLite e limpa os CSVs já importados).

**Escopo:**
- Novo botão/endpoint que, em vez de gerar Excel, importa os CSVs
  pendentes para o banco da região e depois apaga os CSVs já importados.
- Importar a primeira carga do CADOP (de uma planilha Excel) para o banco.
- Criar o esquema de atualização periódica do CADOP.

**Perguntas em aberto:**
- **5.3.1** O botão "Consolidar" atual (gera `.xls`) deve deixar de existir,
  ou os dois convivem (Excel pra conferência manual, banco pra uso pelos
  próximos módulos)?
- **5.3.2** CADOP é atualizado por upload manual de planilha toda vez, ou
  existe alguma extração automática também?
- **5.3.3** O que exatamente é o "campo de manutenção de status" do CADOP
  citado no rascunho original — quem edita, com que opções de status?

---

### Fase 4 — Dimensionamento, Aderência e Planejamento de Férias

**Objetivo:** primeiros módulos que consomem o banco (CADOP + Evento do
Usuário).

**Escopo:**
- **Dimensionamento:** regras e tabela cruzando CADOP x Evento do Usuário
  para calcular/comparar necessidade de HC.
- **Aderência:** nova pasta/módulo para controle diário, alimentada pelos
  dados do Dimensionamento.
- **Planejamento de Férias:** usa a tabela CADOP.

**Perguntas em aberto — este é o bloco menos detalhado do rascunho original,
precisa de uma conversa dedicada antes de codar:**
- **5.4.1** Dimensionamento: quais são as regras exatas de cálculo? (Existe
  algo parecido pronto em `Planejamento_EDP_ES` — a skill "forecast"/Erlang C
  mencionada no projeto de HC — é a mesma lógica ou é outra?)
- **5.4.2** Aderência: quais métricas exatamente ("controle diário" de quê —
  aderência de horário, de meta, de HC planejado vs realizado)?
- **5.4.3** Planejamento de Férias: qual a regra de elegibilidade/bloqueio de
  férias que vem do CADOP?

---

### Fase 5 — Qualidade

**Objetivo:** módulos de Qualidade (upload de planilha → banco → dashboard).

**Escopo:**
- Import de planilhas Excel específicas por módulo, pro banco.
- Dashboards: EDP Online, Monitoria, Ouvidoria/Reclamação, Inconsistência.

**Perguntas em aberto:**
- **5.5.1** Para cada um dos 4 módulos, preciso de um exemplo real da
  planilha de entrada (colunas, formato) antes de desenhar a importação.
- **5.5.2** "Ouvidorias e Reclamações (duas coisas diferentes)" — quais são
  as duas fontes/planilhas e o que diferencia uma da outra?
- **5.5.3** Inconsistência tem duas planilhas (*Alteração de Titularidade* e
  *Notas Improcedentes*) — viram duas telas separadas ou uma tela com filtro?

---

### Fase 6 — RH

**Objetivo:** import de dados do RH e integração com a Aderência.

**Status do rascunho original:** "totalmente em desenvolvimento pendente,
terá uma fase somente dele" — ou seja, ainda não há nenhuma definição.

**Perguntas em aberto:**
- **5.6.1** Quais dados de RH exatamente (folha de ponto, férias, quadro de
  pessoal, afastamentos)?
- **5.6.2** De onde vêm — upload de planilha, outro sistema, extração como o
  Octagora?

---

### Fase 7 — API online

**Objetivo:** "compilar os dados para possível sistema de API online" —
ainda é uma ideia, não uma especificação.

**Perguntas em aberto:**
- **5.7.1** "Online" significa hospedado em algum servidor da empresa
  (intranet), ou publicamente acessível?
- **5.7.2** Essa API seria consumida por quem — outros sistemas internos,
  um dashboard de BI, outra equipe?
- **5.7.3** Isso implica finalmente precisar de autenticação (a esta altura,
  entre usuários diferentes de verdade, não só a senha do Octagora)?

## 6. Requisitos para rodar localmente (checklist)

- [x] Python 3.11+ com `venv` (`install.bat` cria em `.venv/`)
- [x] Google Chrome instalado (Selenium usa o Chrome real via Selenium
      Manager, sem precisar baixar chromedriver à parte)
- [x] Node.js + npm (frontend Vite/React)
- [x] Usuário e senha do Octagora, cadastrados pela aba Configurações
      (não ficam em nenhum arquivo do repositório)
- [ ] A partir da Fase 2: nenhum requisito novo (SQLite não precisa de
      serviço/instalação separada — é só um arquivo)

## 7. Cronograma (estimativa a validar)

| Fase | Descrição | Depende de | Estimativa |
|---|---|---|---|
| 1 | Separação SP/ES, limpeza de escopo | — | ✅ Concluída |
| 2 | Modelagem do banco | Fase 1 | A estimar após responder 5.2.x |
| 3 | Importação Octagora + CADOP | Fase 2 | A estimar |
| 4 | Dimensionamento + Aderência + Férias | Fase 3 | A estimar (bloco mais incerto — depende de 5.4.x) |
| 5 | Qualidade | Fase 3 | A estimar (depende de exemplos de planilha — 5.5.x) |
| 6 | RH | Fase 3 | A estimar (quase tudo em aberto — 5.6.x) |
| 7 | API online | Fases 3–6 | A estimar (depende de definir o objetivo — 5.7.x) |

> Não dá para estimar prazo em dias/semanas de forma responsável enquanto as
> perguntas em aberto de cada fase não forem respondidas — o cronograma acima
> é a ordem de dependência, não uma data.

## 8. Log de decisões

| Data | Decisão | Motivo |
|---|---|---|
| 2026-09-22 | Remover Tempo Real (SLA) do projeto | Fora do escopo definido nesta arquitetura |
| 2026-09-22 | Remover "Consolidado Geral (SP + ES)" | SP e ES devem ser ambientes 100% separados, sem consolidação cruzada |
| 2026-09-22 | Banco de dados será SQLite (local, sem serviço externo) | Simplicidade de instalação — mantém o `install.bat` funcionando sem dependências extras |
| 2026-09-22 | Menu lateral replica todos os grupos do `Planejamento_Online` | Paridade visual, mesmo com módulos ainda não implementados |
