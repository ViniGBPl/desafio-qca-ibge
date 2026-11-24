"""Ponto de entrada da aplicação."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ibge_coleta.app import criar_aplicacao  # noqa: E402
from ibge_coleta.cli import executar_menu  # noqa: E402
from ibge_coleta.clients.agregados_api import AgregadosAPIClient  # noqa: E402
from ibge_coleta.clients.ibge_api import IBGEAPIClient  # noqa: E402


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # evita poluir o menu com logs HTTP

    with IBGEAPIClient() as api, AgregadosAPIClient() as agregados:
        return executar_menu(criar_aplicacao(api, agregados))


if __name__ == "__main__":
    sys.exit(main())
