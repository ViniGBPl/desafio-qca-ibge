"""Ponto de entrada e raiz de composição da aplicação.

Este é o único lugar que conhece as implementações concretas (httpx, Playwright,
BeautifulSoup, Excel); todas as outras camadas dependem apenas de abstrações.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ibge_coleta.aplicacao.app import AplicacaoColeta  # noqa: E402
from ibge_coleta.apresentacao.cli import executar_menu  # noqa: E402
from ibge_coleta.infraestrutura.clients.agregados_api import AgregadosAPIClient  # noqa: E402
from ibge_coleta.infraestrutura.clients.ibge_api import IBGEAPIClient  # noqa: E402
from ibge_coleta.infraestrutura.clients.portal import PortalPlaywright  # noqa: E402
from ibge_coleta.infraestrutura.exportacao.exporter import ExportadorExcel  # noqa: E402
from ibge_coleta.infraestrutura.exportacao.resumo import GeradorResumo  # noqa: E402
from ibge_coleta.infraestrutura.parsers.cidade_parser import CidadeParser  # noqa: E402


def criar_aplicacao(api: IBGEAPIClient, agregados: AgregadosAPIClient) -> AplicacaoColeta:
    """Monta a aplicação com as implementações reais."""
    return AplicacaoColeta(
        localidades=api,
        fabrica_fonte_html=PortalPlaywright,
        parser=CidadeParser(),
        exportador=ExportadorExcel(gerador_resumo=GeradorResumo()),
        fonte_pib=agregados,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # evita poluir o menu com logs HTTP

    with IBGEAPIClient() as api, AgregadosAPIClient() as agregados:
        return executar_menu(criar_aplicacao(api, agregados))


if __name__ == "__main__":
    sys.exit(main())
