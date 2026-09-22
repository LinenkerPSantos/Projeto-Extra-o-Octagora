"""
Extração — "Extrair Tudo": para cada dia do intervalo, extrai Sumário e
Detalhe de Tempos de Protocolo, para a região indicada (ES ou SP).

Arquivos gerados (um par por dia): downloads/{REGIAO}/sumario{DDMMYYYY}.csv, detalhe{DDMMYYYY}.csv
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.base import OctagoraBase
import config
from scripts.tempoprotocolo_sumario import _extract as _extract_sumario, _date_range
from scripts.tempoprotocolo_detalhe import _extract as _extract_detalhe


def run(regiao: str = "ES", date_start: str = None, date_end: str = None, log=print) -> dict:
    regiao = (regiao or "ES").upper()

    if not date_start:
        date_start = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    if not date_end:
        date_end = date_start

    dias = _date_range(date_start, date_end)
    total = len(dias)

    log(f"[Extrair Tudo-{regiao}] Iniciando extração de {dias[0]} até {dias[-1]} ({total} dia(s))...")

    downloads_dir = config.get_regiao(regiao)["downloads_dir"]
    bot = OctagoraBase(log_callback=log, downloads_dir=downloads_dir)
    resultados: dict = {}
    try:
        bot.login(regiao=regiao)
        bot.human_pause(2, 4, "após login")
        for i, dia in enumerate(dias, start=1):
            if i > 1:
                bot.human_pause(1.5, 3.5, "entre dias")
            log(f"[Extrair Tudo-{regiao}] Dia {i}/{total} — {dia}...")
            sumario = _extract_sumario(bot, dia, log, regiao)
            bot.human_pause(1, 2.5, "entre Sumário e Detalhe")
            detalhe = _extract_detalhe(bot, dia, log, regiao)
            resultados[dia] = {"sumario": sumario, "detalhe": detalhe}
    finally:
        bot.quit()

    falhas = [dia for dia, r in resultados.items() if not r["sumario"] or not r["detalhe"]]
    if falhas:
        log(f"[Extrair Tudo-{regiao}] [AVISO] Dia(s) com falha: {', '.join(falhas)}")
    else:
        log(f"[Extrair Tudo-{regiao}] ✓ Extração concluída para todos os dias.")

    return resultados


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extrai Sumário + Detalhe (ES ou SP) para um intervalo de datas")
    parser.add_argument("--regiao", default="ES", choices=["ES", "SP"], help="Região (padrão: ES)")
    parser.add_argument("--date-start", default=None, help="DD/MM/YYYY — início do intervalo (padrão: ontem)")
    parser.add_argument("--date-end", default=None, help="DD/MM/YYYY — fim do intervalo (padrão: igual a --date-start)")
    args = parser.parse_args()

    resultados = run(regiao=args.regiao, date_start=args.date_start, date_end=args.date_end)
    ok = all(r["sumario"] and r["detalhe"] for r in resultados.values())
    if ok:
        print(f"Sucesso: {len(resultados)} dia(s) extraído(s).")
    else:
        print("Falha na extração de um ou mais dias.")
        sys.exit(1)
