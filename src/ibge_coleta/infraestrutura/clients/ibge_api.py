"""Cliente da API de Localidades do IBGE (Etapa A)."""

import logging
from typing import Any

import httpx

from ibge_coleta.config import API_BASE_URL, HTTP_TIMEOUT_S
from ibge_coleta.dominio.exceptions import IBGEAPIError
from ibge_coleta.dominio.models import Estado, Municipio
from ibge_coleta.infraestrutura.clients.http_base import ClienteHTTPIBGE
from ibge_coleta.utils.texto import chave_ordenacao

logger = logging.getLogger(__name__)


class IBGEAPIClient(ClienteHTTPIBGE):
    """Consulta estados e municípios na API de Localidades."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: float = HTTP_TIMEOUT_S,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout, transport=transport)

    def listar_estados(self) -> list[Estado]:
        """Retorna todos os estados, ordenados por nome."""
        caminho = "/estados"
        dados = self._get_json(caminho)
        try:
            estados = [
                Estado(sigla=e["sigla"], nome=e["nome"], regiao=e["regiao"]["nome"]) for e in dados
            ]
        except (KeyError, TypeError, AttributeError) as e:
            raise self._formato_inesperado(caminho, e) from e
        return sorted(estados, key=lambda e: chave_ordenacao(e.nome))

    def listar_municipios(self, estado: Estado) -> list[Municipio]:
        """Retorna os municípios da UF, ordenados por nome."""
        caminho = f"/estados/{estado.sigla}/municipios"
        dados = self._get_json(caminho)
        if not dados:
            raise IBGEAPIError(f"Nenhum município retornado para a UF {estado.sigla}")

        try:
            municipios = [self._converter_municipio(m, estado) for m in dados]
        except (KeyError, TypeError, AttributeError) as e:
            raise self._formato_inesperado(caminho, e) from e
        return sorted(municipios, key=lambda m: chave_ordenacao(m.nome))

    @staticmethod
    def _converter_municipio(dado: dict[str, Any], estado: Estado) -> Municipio:
        uf_info = _extrair_uf(dado)
        return Municipio(
            codigo_ibge=str(dado["id"]),
            nome=dado["nome"],
            uf=uf_info["sigla"] if uf_info else estado.sigla,
            regiao=uf_info["regiao"]["nome"] if uf_info else estado.regiao,
        )


def _extrair_uf(dado: dict[str, Any]) -> dict[str, Any] | None:
    """Busca a UF dentro da hierarquia do município.

    Alguns municípios recentes vêm com 'microrregiao' nula; nesse caso
    usamos o caminho alternativo por 'regiao-imediata'.
    """
    micro = dado.get("microrregiao")
    if micro:
        return micro["mesorregiao"]["UF"]

    imediata = dado.get("regiao-imediata")
    if imediata:
        return imediata["regiao-intermediaria"]["UF"]

    logger.warning("Município %s sem hierarquia de UF na resposta", dado.get("nome"))
    return None
