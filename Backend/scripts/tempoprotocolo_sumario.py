"""
Extração Octagora: Tempos de Protocolo — Base Sumário (Agência - ES ou SP)
Tabela origem : tbSummary
Arquivo gerado: downloads/{REGIAO}/sumario{DDMMYYYY}.csv  ex: downloads/SP/sumario29042026.csv (um por dia)
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from scripts.base import OctagoraBase


# ── Utilitários de data ─────────────────────────────────────────────────

def _date_range(date_start: str, date_end: str) -> list[str]:
    """Gera lista de datas DD/MM/YYYY de date_start até date_end (inclusive)."""
    d1 = datetime.strptime(date_start, "%d/%m/%Y")
    d2 = datetime.strptime(date_end, "%d/%m/%Y")
    if d2 < d1:
        d1, d2 = d2, d1
    dias = []
    atual = d1
    while atual <= d2:
        dias.append(atual.strftime("%d/%m/%Y"))
        atual += timedelta(days=1)
    return dias


# ── Ponto de entrada principal ─────────────────────────────────────────

def run(regiao: str = "ES", date: str = None, date_start: str = None, date_end: str = None, log=print) -> Path | None:
    """
    regiao            : "ES" ou "SP" — define ambiente, credenciais e pasta de downloads.
    date              : DD/MM/YYYY — atalho para date_start = date_end = date (compat).
    date_start/date_end : DD/MM/YYYY — intervalo (inclusive); padrão: ontem / D-1 para ambos.
    Gera um CSV por dia do intervalo. Retorna o Path do último CSV gerado, ou None em caso de falha.
    """
    regiao = (regiao or "ES").upper()

    if date and not date_start and not date_end:
        date_start = date_end = date

    if not date_start:
        date_start = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    if not date_end:
        date_end = date_start

    dias = _date_range(date_start, date_end)
    total = len(dias)

    log(f"[Sumário-{regiao}] Iniciando extração de {dias[0]} até {dias[-1]} ({total} dia(s))...")

    downloads_dir = config.get_regiao(regiao)["downloads_dir"]
    bot = OctagoraBase(log_callback=log, downloads_dir=downloads_dir)
    try:
        bot.login(regiao=regiao)
        bot.human_pause(2, 4, "após login")
        ultimo = None
        for i, dia in enumerate(dias, start=1):
            if i > 1:
                bot.human_pause(1.5, 3.5, "entre dias")
            log(f"[Sumário-{regiao}] Dia {i}/{total} — {dia}...")
            resultado = _extract(bot, dia, log, regiao)
            if resultado:
                ultimo = resultado
        return ultimo
    finally:
        bot.quit()


# ── Lógica de extração ─────────────────────────────────────────────────

def _extract(bot: OctagoraBase, date: str, log, regiao: str = "ES") -> Path | None:
    driver = bot.driver

    # ── 1. Navegar: Relatórios → Tempos dos Protocolos ────────────
    log(f"[Sumário-{regiao}] Abrindo menu Relatórios...")

    # HTML: <a href="#"><p>Relatórios<i class="fas fa-angle-left right"></i></p></a>
    bot._click(By.XPATH, "//a[.//p[contains(text(),'Relatórios')]]")
    time.sleep(1)

    # HTML: <a href="/Edp/TicketTime/Report"><p>Tempos dos Protocolos</p></a>
    bot._click(By.XPATH, "//a[@href='/Edp/TicketTime/Report']")
    time.sleep(3)
    log(f"[Sumário-{regiao}] Tela Tempos de Protocolo aberta.")

    # ── 2. Filtros ─────────────────────────────────────────────────

    # Radio "Criado" — HTML: <input type="radio" id="DateTypeS" value="S" checked>
    # Já vem selecionado por padrão; garante que está marcado
    try:
        radio = driver.find_element(By.ID, "DateTypeS")
        if not radio.is_selected():
            radio.click()
    except Exception:
        log(f"[Sumário-{regiao}] [AVISO] Radio 'Criado' não encontrado, continuando.")

    # Campo de data — HTML: <input id="dtFilter" data-range="">
    # Formato esperado: "29/04/2026 - 29/04/2026"
    log(f"[Sumário-{regiao}] Definindo data: {date}...")
    date_field = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "dtFilter"))
    )
    date_field.click()          # abre o daterangepicker
    time.sleep(0.5)
    date_field.send_keys(Keys.CONTROL + "a")   # seleciona tudo
    date_field.send_keys(Keys.DELETE)           # limpa
    date_field.send_keys(f"{date} - {date}")    # digita o intervalo
    time.sleep(0.3)

    # Botão OK do datepicker — HTML: <button class="applyBtn btn btn-sm btn-primary">OK</button>
    bot._click(By.CSS_SELECTOR, "button.applyBtn.btn-primary")
    time.sleep(0.5)

    # Campo Regulado — HTML: <select id="flIsRegulated"><option value="A">Todos</option>
    Select(driver.find_element(By.ID, "flIsRegulated")).select_by_value("A")

    # ── 3. Clica em Filtrar e aguarda a tabela carregar ────────────
    # HTML: <input type="button" id="btnFilter" value="Filtrar">
    # O botão fica disabled durante o carregamento e volta ao normal quando termina
    log(f"[Sumário-{regiao}] Filtrando...")
    driver.find_element(By.ID, "btnFilter").click()

    time.sleep(1.5)  # aguarda o botão ficar disabled
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, "btnFilter"))
    )
    log(f"[Sumário-{regiao}] Tabela carregada.")

    # ── 4. Exportar CSV do Sumário ─────────────────────────────────
    # HTML: <button onclick="tableToCSV('tbSummary')" title="Exportar (CSV)">
    date_compact = date.replace("/", "")
    bot._clear_download_target(f"sumario{date_compact}.csv")
    log(f"[Sumário-{regiao}] Clicando em Exportar CSV (Sumário)...")
    snapshot = bot._snapshot()
    bot._click(By.XPATH, "//button[@onclick=\"tableToCSV('tbSummary')\"]")

    downloaded = bot._wait_new_file(snapshot, timeout=30)
    if not downloaded:
        log(f"[Sumário-{regiao}] [ERRO] Arquivo não baixado.")
        return None

    final = bot._rename_download(downloaded, f"sumario{date_compact}.csv")
    log(f"[Sumário-{regiao}] ✓ Arquivo salvo: {final.name}")
    return final


# ── Execução direta pelo terminal ──────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extrai Sumário de Tempos de Protocolo (ES ou SP)")
    parser.add_argument("--regiao", default="ES", choices=["ES", "SP"], help="Região (padrão: ES)")
    parser.add_argument("--date", default=None, help="DD/MM/YYYY (padrão: ontem)")
    parser.add_argument("--date-start", default=None, help="DD/MM/YYYY — início do intervalo (padrão: ontem)")
    parser.add_argument("--date-end", default=None, help="DD/MM/YYYY — fim do intervalo (padrão: igual a --date-start)")
    args = parser.parse_args()

    result = run(regiao=args.regiao, date=args.date, date_start=args.date_start, date_end=args.date_end)
    if result:
        print(f"Sucesso: {result}")
    else:
        print("Falha na extração.")
        sys.exit(1)
