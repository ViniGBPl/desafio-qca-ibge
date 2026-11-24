"""Salva o HTML de uma página do portal para uso nos testes.

Uso: python scripts/salvar_fixture.py pe recife
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from ibge_coleta.config import PAGE_TIMEOUT_MS, PORTAL_BASE_URL  # noqa: E402

uf, slug = (sys.argv[1], sys.argv[2]) if len(sys.argv) == 3 else ("pe", "recife")
url = f"{PORTAL_BASE_URL}/{uf}/{slug}.html"
destino = RAIZ / "tests" / "fixtures" / f"{slug}.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
    # Aguarda a verificação anti-bot (Cloudflare) terminar
    page.wait_for_function("!document.title.includes('Just a moment')", timeout=PAGE_TIMEOUT_MS)
    page.wait_for_timeout(5_000)
    print("Título:", page.title())
    destino.write_text(page.content(), encoding="utf-8")
    print(f"Salvo em {destino} ({destino.stat().st_size // 1024} KB)")
    browser.close()
