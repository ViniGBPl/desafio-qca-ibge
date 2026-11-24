"""Ponto de entrada da aplicação."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ibge_coleta.cli import main  # noqa: E402

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # evita poluir o menu com logs HTTP
    sys.exit(main())
