"""Cliente da API de Agregados do IBGE: PIB dos municípios (diferencial)."""

import logging
from typing import Any

import httpx

from ibge_coleta.config import AGREGADO_PIB, AGREGADOS_BASE_URL, HTTP_TIMEOUT_S, VARIAVEL_PIB
from ibge_coleta.dominio.exceptions import IBGEAPIError
from ibge_coleta.dominio.models import IndicadorPIB
from ibge_coleta.infraestrutura.clients.http_base import ClienteHTTPIBGE
from ibge_coleta.utils.texto import extrair_ano

logger = logging.getLogger(__name__)


class AgregadosAPIClient(ClienteHTTPIBGE):
    """Consulta o PIB a preços correntes (último ano disponível) por município."""

    def __init__(
        self,
        base_url: str = AGREGADOS_BASE_URL,
        timeout: float = HTTP_TIMEOUT_S,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout, transport=transport)

    def obter_pib(self, codigos_ibge: list[str]) -> dict[str, IndicadorPIB]:
        """Retorna {codigo_ibge: IndicadorPIB} para os municípios informados.

        Faz uma única requisição para todos. A API devolve erro 500 para o lote inteiro
        se algum código não existir na série; nesse caso, consulta um a um para não
        perder os demais. Municípios sem dado simplesmente não aparecem no dicionário.
        """
        if not codigos_ibge:
            return {}
        try:
            return self._consultar(codigos_ibge)
        except IBGEAPIError as e:
            if len(codigos_ibge) == 1:
                raise
            logger.warning("Consulta do PIB em lote falhou (%s); consultando um a um", e)

        indicadores: dict[str, IndicadorPIB] = {}
        for codigo in codigos_ibge:
            try:
                indicadores.update(self._consultar([codigo]))
            except IBGEAPIError as e:
                logger.warning("PIB indisponível para o município %s: %s", codigo, e)
        return indicadores

    def _consultar(self, codigos_ibge: list[str]) -> dict[str, IndicadorPIB]:
        caminho = f"/{AGREGADO_PIB}/periodos/-1/variaveis/{VARIAVEL_PIB}"
        dados = self._get_json(caminho, params={"localidades": f"N6[{','.join(codigos_ibge)}]"})
        try:
            return self._interpretar(dados)
        except (KeyError, TypeError, AttributeError) as e:
            raise self._formato_inesperado(caminho, e) from e

    @staticmethod
    def _interpretar(dados: list[dict[str, Any]]) -> dict[str, IndicadorPIB]:
        indicadores: dict[str, IndicadorPIB] = {}
        for variavel in dados:
            for resultado in variavel.get("resultados", []):
                for serie in resultado.get("series", []):
                    codigo = serie["localidade"]["id"]
                    for ano, valor in serie.get("serie", {}).items():
                        indicadores[codigo] = IndicadorPIB(
                            valor_mil_reais=_converter_valor(valor), ano=extrair_ano(ano)
                        )
        return indicadores


def _converter_valor(valor: str | None) -> float | None:
    """A API usa símbolos para dado indisponível ('-', '...', 'X'): viram None."""
    try:
        return float(valor) if valor is not None else None
    except ValueError:
        return None
