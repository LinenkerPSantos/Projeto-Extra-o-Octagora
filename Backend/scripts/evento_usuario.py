"""
Extração: Evento do Usuário — Base Resultado (Agência - ES ou SP)
URL: /Edp/UserEvent/Report
Arquivo gerado: downloads/{REGIAO}/evento{DDMMYYYY}.csv  ex: downloads/SP/evento29042026.csv
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from scripts.base import OctagoraBase


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


def run(regiao: str = "ES", date: str = None, date_start: str = None, date_end: str = None, log=print) -> Path | None:
    regiao = (regiao or "ES").upper()

    if date and not date_start and not date_end:
        date_start = date_end = date

    if not date_start:
        date_start = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    if not date_end:
        date_end = date_start

    dias = _date_range(date_start, date_end)
    total = len(dias)

    log(f"[EventoUsuário-{regiao}] Iniciando extração de {dias[0]} até {dias[-1]} ({total} dia(s))...")

    downloads_dir = config.get_regiao(regiao)["downloads_dir"]
    bot = OctagoraBase(log_callback=log, downloads_dir=downloads_dir)
    try:
        bot.login(regiao=regiao)
        bot.human_pause(2, 4, "após login")
        ultimo = None
        for i, dia in enumerate(dias, start=1):
            if i > 1:
                bot.human_pause(1.5, 3.5, "entre dias")
            log(f"[EventoUsuário-{regiao}] Dia {i}/{total} — {dia}...")
            resultado = _extract(bot, dia, log, regiao)
            if resultado:
                ultimo = resultado
        return ultimo
    finally:
        bot.quit()


def _extract(bot: OctagoraBase, date: str, log, regiao: str = "ES") -> Path | None:
    driver = bot.driver

    # ── 1. Navegar: Relatórios → Eventos do Usuário ───────────────────
    log(f"[EventoUsuário-{regiao}] Abrindo menu Relatórios...")

    # HTML: <a href="#"><p>Relatórios<i class="fas fa-angle-left right"></i></p></a>
    bot._click(By.XPATH, "//a[.//p[contains(text(),'Relatórios')]]")
    time.sleep(1)

    # HTML: <a href="/Edp/UserEvent/Report" class="nav-link"><p>Eventos do usuário</p></a>
    bot._click(By.XPATH, "//a[@href='/Edp/UserEvent/Report']")
    time.sleep(3)
    log(f"[EventoUsuário-{regiao}] Tela Eventos do Usuário aberta.")

    # ── 2. Preencher data ─────────────────────────────────────────────
    # HTML: <input type="text" class="form-control" id="dtFilter" value="29/04/2026">
    # Campo aceita data única no formato DD/MM/YYYY (sem intervalo)
    log(f"[EventoUsuário-{regiao}] Definindo data: {date}...")
    date_field = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "dtFilter"))
    )
    date_field.click()
    time.sleep(0.3)
    date_field.send_keys(Keys.CONTROL + "a")
    date_field.send_keys(Keys.DELETE)
    date_field.send_keys(date)
    time.sleep(0.3)
    # Confirma datepicker se houver; Tab fecha qualquer popup sem confirmar
    try:
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.applyBtn.btn-primary"))
        ).click()
    except Exception:
        date_field.send_keys(Keys.TAB)

    # ── 3. Clicar em Filtrar e aguardar tabela ────────────────────────
    # HTML: <input type="button" class="btn btn-default" id="btnFilter"
    #             onclick="ticketFilter.filter()">
    log(f"[EventoUsuário-{regiao}] Filtrando...")
    driver.find_element(By.ID, "btnFilter").click()

    time.sleep(1.5)  # aguarda o botão ficar disabled
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, "btnFilter"))
    )
    log(f"[EventoUsuário-{regiao}] Tabela carregada.")

    # ── 4. Exportar CSV ───────────────────────────────────────────────
    # HTML: <button type="button" class="btn btn-tool" style="color:green;"
    #             title="Exportar (CSV)" onclick="tableToCSV('tbResult')">
    date_compact = date.replace("/", "")
    bot._clear_download_target(f"evento{date_compact}.csv")
    log(f"[EventoUsuário-{regiao}] Clicando em Exportar CSV...")
    snapshot = bot._snapshot()
    # Tabela pode ser muito longa (Y > 10000px) — JS click ignora interceptações e viewport
    bot._js_click(By.XPATH, "//button[@onclick=\"tableToCSV('tbResult')\"]")

    downloaded = bot._wait_new_file(snapshot, timeout=30)
    if not downloaded:
        log(f"[EventoUsuário-{regiao}] [ERRO] Arquivo não baixado.")
        return None

    final = bot._rename_download(downloaded, f"evento{date_compact}.csv")
    log(f"[EventoUsuário-{regiao}] ✓ Arquivo salvo: {final.name}")
    return final


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extrai Evento do Usuário (ES ou SP)")
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
