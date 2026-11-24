"""Cliente da API de Localidades do IBGE (Etapa A)."""

import logging
from typing import Any

import httpx

from ibge_coleta.config import API_BASE_URL, HTTP_TIMEOUT_S
from ibge_coleta.exceptions import IBGEAPIError
from ibge_coleta.models import Estado, Municipio
from ibge_coleta.utils.texto import chave_ordenacao

logger = logging.getLogger(__name__)


class IBGEAPIClient:
    """Consulta estados e municípios na API de Localidades."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: float = HTTP_TIMEOUT_S) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def __enter__(self) -> "IBGEAPIClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def listar_estados(self) -> list[Estado]:
        """Retorna todos os estados, ordenados por nome."""
        dados = self._get_json("/estados")
        estados = [
            Estado(sigla=e["sigla"], nome=e["nome"], regiao=e["regiao"]["nome"]) for e in dados
        ]
        return sorted(estados, key=lambda e: chave_ordenacao(e.nome))

    def listar_municipios(self, estado: Estado) -> list[Municipio]:
        """Retorna os municípios da UF, ordenados por nome."""
        dados = self._get_json(f"/estados/{estado.sigla}/municipios")
        if not dados:
            raise IBGEAPIError(f"Nenhum município retornado para a UF {estado.sigla}")

        municipios = [self._converter_municipio(m, estado) for m in dados]
        return sorted(municipios, key=lambda m: chave_ordenacao(m.nome))

    def _get_json(self, caminho: str) -> list[dict[str, Any]]:
        try:
            resposta = self._client.get(caminho)
            resposta.raise_for_status()
            dados = resposta.json()
        except httpx.TimeoutException as e:
            raise IBGEAPIError(f"Tempo esgotado ao acessar {caminho}") from e
        except httpx.HTTPStatusError as e:
            raise IBGEAPIError(f"Erro HTTP {e.response.status_code} em {caminho}") from e
        except httpx.RequestError as e:
            raise IBGEAPIError(f"Falha de conexão ao acessar {caminho}: {e}") from e
        except ValueError as e:
            raise IBGEAPIError(f"Resposta inválida (não é JSON) em {caminho}") from e

        if not isinstance(dados, list):
            raise IBGEAPIError(f"Formato inesperado em {caminho}: esperava uma lista")
        return dados

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
