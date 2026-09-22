"""
Helper interno — extração de formulário NPS via Selenium.
Usado pelos scripts formulario_nps_*.py (não é um script autônomo).

Os FORM_TOKEN abaixo (em cada formulario_nps_*.py) foram capturados no
ambiente "Agências - SP" — é o único ambiente onde esses formulários existem
hoje no Octagora (não há herança de legado para ES). Se um dia existirem os
mesmos formulários cadastrados em "Agências - ES", basta descobrir o token
do <option> de lá e chamar extract_nps(..., regiao="ES").
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


def extract_nps(
    form_token: str,
    output_prefix: str,
    regiao: str = "SP",
    date: str = None,
    date_start: str = None,
    date_end: str = None,
    log=print,
) -> Path | None:
    """
    form_token    : valor do <option> no select#idFormToken
    output_prefix : prefixo do arquivo CSV gerado (ex: 'nps_agencias')
    regiao        : "SP" (único ambiente com esses formulários hoje)
    date              : DD/MM/YYYY — atalho para date_start = date_end = date (compat).
    date_start/date_end : DD/MM/YYYY — intervalo (inclusive); padrão: ontem / D-1 para ambos.
    Gera um CSV por dia do intervalo. Retorna o Path do último CSV gerado, ou None em caso de falha.
    """
    regiao = (regiao or "SP").upper()

    if date and not date_start and not date_end:
        date_start = date_end = date

    if not date_start:
        date_start = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    if not date_end:
        date_end = date_start

    dias = _date_range(date_start, date_end)
    total = len(dias)

    label = f"{output_prefix.replace('_', ' ').title()}-{regiao}"
    log(f"[{label}] Iniciando extração de {dias[0]} até {dias[-1]} ({total} dia(s))...")

    downloads_dir = config.get_regiao(regiao)["downloads_dir"]
    bot = OctagoraBase(log_callback=log, downloads_dir=downloads_dir)
    try:
        bot.login(regiao=regiao)
        bot.human_pause(2, 4, "após login")
        ultimo = None
        for i, dia in enumerate(dias, start=1):
            if i > 1:
                bot.human_pause(1.5, 3.5, "entre dias")
            log(f"[{label}] Dia {i}/{total} — {dia}...")
            resultado = _extract(bot, dia, form_token, output_prefix, label, log)
            if resultado:
                ultimo = resultado
        return ultimo
    finally:
        bot.quit()


def _extract(bot: OctagoraBase, date: str, form_token: str, output_prefix: str, label: str, log) -> Path | None:
    driver = bot.driver

    # ── 1. Navegar: Relatórios → Formulários ──────────────────────────
    log(f"[{label}] Abrindo menu Relatórios...")

    # HTML: <a href="#"><p>Relatórios<i class="fas fa-angle-left right"></i></p></a>
    bot._click(By.XPATH, "//a[.//p[contains(text(),'Relatórios')]]")
    time.sleep(1)

    # HTML: <a href="/Edp/FlexForm/Report" class="nav-link"><p>Formulários</p></a>
    bot._click(By.XPATH, "//a[@href='/Edp/FlexForm/Report']")
    time.sleep(3)
    log(f"[{label}] Tela Formulários aberta.")

    # ── 2. Selecionar o formulário pelo token ──────────────────────────
    # HTML: <select class="form-control" id="idFormToken">
    #         <option value="6D3047...">NPS - Agências SP</option> ...
    log(f"[{label}] Selecionando formulário...")
    bot._select_by_value("idFormToken", form_token)
    time.sleep(0.5)

    # ── 3. Preencher intervalo de datas ────────────────────────────────
    # HTML: <input class="form-control" id="DtFilter" name="DtFilter" type="text"
    #             data-range-clear="">
    # Formato esperado: "29/04/2026 - 29/04/2026"
    log(f"[{label}] Definindo data: {date}...")
    date_field = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "DtFilter"))
    )
    date_field.click()
    time.sleep(0.5)
    date_field.send_keys(Keys.CONTROL + "a")
    date_field.send_keys(Keys.DELETE)
    date_field.send_keys(f"{date} - {date}")
    time.sleep(0.3)
    # Confirma o daterangepicker; Tab fecha sem confirmar se não houver botão
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.applyBtn.btn-primary"))
        ).click()
    except Exception:
        date_field.send_keys(Keys.TAB)

    # ── 4. Clicar em Filtrar e aguardar tabela ─────────────────────────
    # HTML: <button type="submit" class="btn btn-default" id="Filtro"
    #             onclick="$('#ActionButton').val('Filtro')">Filtrar</button>
    log(f"[{label}] Filtrando...")
    btn_filtro = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "Filtro"))
    )
    btn_filtro.click()

    time.sleep(1.5)  # aguarda o botão ficar disabled
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, "Filtro"))
    )
    log(f"[{label}] Tabela carregada.")

    # ── 5. Exportar CSV ────────────────────────────────────────────────
    # HTML: <button type="button" class="btn btn-tool" style="color:green;"
    #             title="Exportar (CSV)" onclick="tableToCSV('tbResult')">
    date_compact = date.replace("/", "")
    bot._clear_download_target(f"{output_prefix}{date_compact}.csv")
    log(f"[{label}] Clicando em Exportar CSV...")
    snapshot = bot._snapshot()
    bot._click(By.XPATH, "//button[@onclick=\"tableToCSV('tbResult')\"]")

    downloaded = bot._wait_new_file(snapshot, timeout=30)
    if not downloaded:
        log(f"[{label}] [ERRO] Arquivo não baixado.")
        return None

    final = bot._rename_download(downloaded, f"{output_prefix}{date_compact}.csv")
    log(f"[{label}] ✓ Arquivo salvo: {final.name}")
    return final
