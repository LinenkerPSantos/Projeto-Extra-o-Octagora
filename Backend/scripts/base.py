"""
Classe base compartilhada pelos scripts de extração.
Responsável por: iniciar o Chrome, fazer login, helpers de click/fill/download.
"""

import sys
import time
import random
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class OctagoraBase:
    def __init__(self, log_callback=None, headless: bool = None, downloads_dir: Path = None):
        self.log = log_callback or print
        self.downloads = downloads_dir or config.DOWNLOADS_DIR
        headless = config.OCTAGORA_HEADLESS if headless is None else headless
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 25)

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "download.default_directory": str(self.downloads),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        })
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)
        if not headless:
            driver.maximize_window()
        return driver

    # ------------------------------------------------------------------
    # Helpers de interação
    # ------------------------------------------------------------------

    def _click(self, by, value, timeout=25):
        el = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        el.click()
        return el

    def _js_click(self, by, value, timeout=25):
        """Clica via JavaScript — ignora sobreposições e elementos fora da viewport."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", el)
        return el

    def _fill(self, by, value, text, clear=True):
        el = self.wait.until(EC.presence_of_element_located((by, value)))
        if clear:
            el.clear()
        el.send_keys(text)
        return el

    def _select_by_value(self, element_id: str, option_value: str):
        el = self.wait.until(EC.presence_of_element_located((By.ID, element_id)))
        Select(el).select_by_value(option_value)

    def human_pause(self, min_s: float = 1.5, max_s: float = 3.5, label: str = None):
        """Pausa curta e aleatória entre atividades, para não bater requisições
        em sequência direta e imitar um ritmo humano de navegação."""
        delay = random.uniform(min_s, max_s)
        if label:
            self.log(f"  ... aguardando {delay:.1f}s ({label})")
        time.sleep(delay)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, regiao: str = "ES", env: str = None, user: str = None, password: str = None):
        """Faz login no Octagora. `regiao` ("ES" ou "SP") define o ambiente e as
        credenciais padrão a partir de config.get_regiao — sobrepostas por env/user/
        password quando informados explicitamente."""
        cfg = config.get_regiao(regiao)

        self.log("Acessando Octagora...")
        self.driver.get(config.OCTAGORA_URL)
        time.sleep(2)

        # HTML: <select id="IdArea"><option value="199">Agências - SP</option>
        env_str = env or cfg["env"]
        el = self.wait.until(EC.presence_of_element_located((By.ID, "IdArea")))
        Select(el).select_by_visible_text(env_str)
        self.log(f"  Ambiente: {env_str}")

        # HTML: <input id="Login" type="text">
        self._fill(By.ID, "Login", user or cfg["user"])

        # HTML: <input id="Password" type="password">
        self._fill(By.ID, "Password", password or cfg["password"])

        # HTML: <button id="btnLogin">Entrar</button>
        self._click(By.ID, "btnLogin")

        self.log("Login realizado. Aguardando carregamento...")
        time.sleep(4)

    # ------------------------------------------------------------------
    # Helpers de download
    # ------------------------------------------------------------------

    def _snapshot(self) -> set:
        """Retorna conjunto de todos os arquivos atuais na pasta de downloads."""
        return set(self.downloads.glob("*"))

    def _wait_new_file(self, before: set, timeout: int = 30) -> Path | None:
        """Aguarda um novo arquivo aparecer na pasta de downloads."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            after = set(self.downloads.glob("*"))
            new_files = {
                f for f in (after - before)
                if not str(f).endswith(".crdownload") and f.is_file()
            }
            if new_files:
                return max(new_files, key=lambda f: f.stat().st_mtime)
            time.sleep(0.5)
        self.log("  [AVISO] Timeout aguardando arquivo de download.")
        return None

    def _rename_download(self, path: Path, new_name: str) -> Path:
        dest = self.downloads / new_name
        if dest.exists():
            dest.unlink()
        path.rename(dest)
        return dest

    def _clear_download_target(self, final_name: str):
        """Remove o arquivo destino e qualquer .crdownload pendente antes de baixar.
        Evita que o Chrome acrescente ' (1)' quando o arquivo já existe."""
        target = self.downloads / final_name
        if target.exists():
            target.unlink()
            self.log(f"  [INFO] Arquivo anterior removido: {final_name}")
        for crdownload in self.downloads.glob("*.crdownload"):
            try:
                crdownload.unlink()
            except Exception:
                pass

    # ------------------------------------------------------------------

    def quit(self):
        self.driver.quit()
