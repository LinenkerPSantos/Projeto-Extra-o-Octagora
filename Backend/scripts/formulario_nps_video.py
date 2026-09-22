"""
Extração: Formulário — NPS Vídeo e Totem de Senhas SP — Resultado
URL: /Edp/FlexForm/Report
Arquivo gerado: downloads/SP/nps_video{DDMMYYYY}.csv
Disponível apenas para SP (formulário não existe em Agências - ES).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts._formulario_extract import extract_nps

# HTML: <option value="6F31...">NPS - Vídeo e Totem de Senhas - SP</option>
FORM_TOKEN = "6F31784359644856634878773346686A625447326F673D3D"


def run(regiao: str = "SP", date: str = None, date_start: str = None, date_end: str = None, log=print) -> Path | None:
    return extract_nps(
        form_token=FORM_TOKEN,
        output_prefix="nps_video",
        regiao=regiao,
        date=date,
        date_start=date_start,
        date_end=date_end,
        log=log,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extrai NPS Vídeo e Totem SP")
    parser.add_argument("--regiao", default="SP", choices=["SP"], help="Região (apenas SP)")
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
