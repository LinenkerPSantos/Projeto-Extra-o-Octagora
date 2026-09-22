"""
Coleta a fila SLA do Dashboard Presencial (Tempo Real) e salva um JSON —
não é um relatório com filtro de data, é uma foto do momento da execução.

Arquivo gerado: downloads/{REGIAO}/tempo_real.json
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from scripts.base import OctagoraBase

DASHBOARD_URL = "https://adm.octagora.com/Edp/DashboardInPerson/Report"

LIMITE_CRITICO_MIN = 30
LIMITE_ALTO_MIN    = 20
LIMITE_ATENCAO_MIN = 10


# ── helpers ───────────────────────────────────────────────────────────────────

def _espera_para_minutos(hms: str) -> float:
    try:
        h, m, s = hms.strip().split(":")
        return int(h) * 60 + int(m) + int(s) / 60
    except Exception:
        return 0.0


def _nivel_risco(minutos: float) -> str:
    if minutos >= LIMITE_CRITICO_MIN: return "CRÍTICO"
    if minutos >= LIMITE_ALTO_MIN:    return "ALTO RISCO"
    if minutos >= LIMITE_ATENCAO_MIN: return "ATENÇÃO"
    return "NORMAL"


def _fmt_min(minutos: float) -> str:
    return f"{int(minutos // 60):02d}:{int(minutos % 60):02d}"


def _classe_para_status(div) -> str:
    classes = div.get("class", []) if div else []
    if "slaLate"  in classes: return "Atrasado"
    if "slaAlert" in classes: return "Alerta"
    if "slaOk"    in classes: return "OK"
    return "Desconhecido"


# ── parse do HTML ─────────────────────────────────────────────────────────────

def parse_html(html: str) -> list:
    soup   = BeautifulSoup(html, "html.parser")
    tabela = soup.find("table", {"id": "tbResultSla"})
    if not tabela:
        return []

    linhas = []
    for tr in tabela.select("tbody tr.dashboardInPersonRowSla"):
        colunas = tr.find_all("td")
        if len(colunas) < 4:
            continue

        div_status = colunas[0].find("div", class_="dashboardInPersonStatus")
        status     = _classe_para_status(div_status)
        unidade    = colunas[1].get_text(strip=True)
        protocolo  = " ".join(colunas[2].get_text(" ", strip=True).split()).replace("📄", "").strip()
        span_serv  = colunas[2].find("span", title=True)
        servico    = span_serv["title"] if span_serv else ""
        espera     = colunas[3].get_text(strip=True)
        minutos    = _espera_para_minutos(espera)

        linhas.append({
            "status":    status,
            "unidade":   unidade,
            "protocolo": protocolo,
            "servico":   servico,
            "espera":    espera,
            "minutos":   round(minutos, 2),
            "risco":     _nivel_risco(minutos),
        })

    return linhas


# ── análise por agência ───────────────────────────────────────────────────────

def analisar_agencias(linhas: list) -> list:
    grupos = defaultdict(lambda: {
        "tickets": 0, "max_min": 0.0, "soma_min": 0.0,
        "atrasado": 0, "alerta": 0, "ok": 0, "criticos": 0,
    })

    for l in linhas:
        g = grupos[l["unidade"]]
        g["tickets"]  += 1
        g["soma_min"] += l["minutos"]
        if l["minutos"] > g["max_min"]:
            g["max_min"] = l["minutos"]
        if   l["status"] == "Atrasado": g["atrasado"] += 1
        elif l["status"] == "Alerta":   g["alerta"]   += 1
        else:                           g["ok"]        += 1
        if l["minutos"] >= LIMITE_CRITICO_MIN:
            g["criticos"] += 1

    ORDEM = {"CRÍTICO": 0, "ALTO RISCO": 1, "ATENÇÃO": 2, "NORMAL": 3}
    resultado = []
    for agencia, g in grupos.items():
        media = g["soma_min"] / g["tickets"] if g["tickets"] else 0
        risco = _nivel_risco(g["max_min"])
        resultado.append({
            "agencia":    agencia,
            "risco":      risco,
            "tickets":    g["tickets"],
            "espera_max": _fmt_min(g["max_min"]),
            "espera_med": _fmt_min(media),
            "atrasado":   g["atrasado"],
            "alerta":     g["alerta"],
            "ok":         g["ok"],
            "criticos":   g["criticos"],
            "max_min":    round(g["max_min"], 2),
        })

    resultado.sort(key=lambda x: (-x["max_min"], ORDEM.get(x["risco"], 9)))
    return resultado


# ── coleta via Selenium ───────────────────────────────────────────────────────

def _coletar_tabela(bot: OctagoraBase, regiao: str, log) -> str:
    driver = bot.driver
    wait   = WebDriverWait(driver, 60)

    log(f"[TempoReal-{regiao}] Navegando para Dashboard Presencial...")
    driver.get(DASHBOARD_URL)
    time.sleep(2)

    log(f"[TempoReal-{regiao}] Procurando botão 'Filtrar'...")
    try:
        btn = wait.until(EC.element_to_be_clickable((By.ID, "btnFilter")))
        btn.click()
        log(f"[TempoReal-{regiao}] Filtro aplicado. Aguardando dados...")
    except TimeoutException:
        log(f"[TempoReal-{regiao}] [AVISO] Botão 'Filtrar' não encontrado em 60s.")

    log(f"[TempoReal-{regiao}] Aguardando linhas na tabela #tbResultSla...")
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "tbody tr.dashboardInPersonRowSla")
        ))
    except TimeoutException:
        log(f"[TempoReal-{regiao}] [AVISO] Nenhuma linha encontrada após 60s (fila vazia ou página não carregou).")
        return ""

    time.sleep(2)

    log(f"[TempoReal-{regiao}] Ajustando para 100 registros por página...")
    try:
        sel = driver.find_element(By.CSS_SELECTOR, "select[name='tbResultSla_length']")
        Select(sel).select_by_value("100")
        time.sleep(1.5)
    except Exception as e:
        log(f"[TempoReal-{regiao}] [AVISO] Não foi possível ajustar paginação: {e}")

    log(f"[TempoReal-{regiao}] Extraindo HTML da tabela...")
    try:
        tabela = driver.find_element(By.ID, "tbResultSla")
        html   = tabela.get_attribute("outerHTML")
        count  = html.count("dashboardInPersonRowSla")
        log(f"[TempoReal-{regiao}] {count} registros capturados.")
        return html
    except Exception as e:
        log(f"[TempoReal-{regiao}] [ERRO] Não foi possível obter o HTML: {e}")
        return ""


# ── ponto de entrada ──────────────────────────────────────────────────────────

def run(regiao: str = "SP", log=print, **_ignored) -> Path | None:
    """`**_ignored` absorve date_start/date_end — o job runner sempre os envia,
    mas este relatório não usa filtro de data (é uma foto do momento)."""
    regiao = (regiao or "SP").upper()
    cfg = config.get_regiao(regiao)

    log(f"[TempoReal-{regiao}] Iniciando coleta da fila SLA...")

    bot = OctagoraBase(log_callback=log, headless=True, downloads_dir=cfg["downloads_dir"])
    try:
        bot.login(regiao=regiao)
        html = _coletar_tabela(bot, regiao, log)
    finally:
        bot.quit()

    if not html:
        log(f"[TempoReal-{regiao}] [ERRO] Nenhum HTML capturado — encerrando sem salvar dados.")
        return None

    linhas = parse_html(html)
    agencias = analisar_agencias(linhas)
    ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    totais = {
        "total":             len(linhas),
        "critico":           sum(1 for l in linhas if l["risco"] == "CRÍTICO"),
        "alto_risco":        sum(1 for l in linhas if l["risco"] == "ALTO RISCO"),
        "atencao":           sum(1 for l in linhas if l["risco"] == "ATENÇÃO"),
        "normal":            sum(1 for l in linhas if l["risco"] == "NORMAL"),
        "atrasados":         sum(1 for l in linhas if l["status"] == "Atrasado"),
        "agencias_em_risco": sum(1 for a in agencias if a["risco"] in ("CRÍTICO", "ALTO RISCO")),
    }

    dados = {
        "timestamp": ts,
        "regiao":    regiao,
        "totais":    totais,
        "agencias":  agencias,
        "linhas":    linhas,
    }

    output = cfg["downloads_dir"] / "tempo_real.json"
    output.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"[TempoReal-{regiao}] ✓ Coleta concluída às {ts} — {len(linhas)} registros, {len(agencias)} agências.")
    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Coleta a fila SLA do Dashboard Presencial (Tempo Real)")
    parser.add_argument("--regiao", default="SP", choices=["ES", "SP"], help="Região (padrão: SP)")
    parser.add_argument("--date-start", default=None, help="Ignorado — Tempo Real não usa filtro de data")
    parser.add_argument("--date-end", default=None, help="Ignorado — Tempo Real não usa filtro de data")
    args = parser.parse_args()

    result = run(regiao=args.regiao)
    if result:
        print(f"Sucesso: {result}")
    else:
        print("Falha na coleta.")
        sys.exit(1)
