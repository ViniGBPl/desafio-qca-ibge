"""Base comum aos clientes HTTP das APIs do IBGE (httpx)."""

from typing import Any, Self

import httpx

from ibge_coleta.config import HTTP_TIMEOUT_S
from ibge_coleta.exceptions import IBGEAPIError


class ClienteHTTPIBGE:
    """Gerencia a conexão httpx e converte falhas HTTP/JSON em IBGEAPIError.

    As APIs de Localidades e de Agregados herdam desta classe, o que evita
    duplicar o tratamento de timeout, erro HTTP, falha de conexão e JSON inválido.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = HTTP_TIMEOUT_S,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # 'transport' permite simular respostas da API nos testes (httpx.MockTransport).
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _get_json(self, caminho: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        try:
            resposta = self._client.get(caminho, params=params)
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
