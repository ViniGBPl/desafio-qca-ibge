"""Orquestra a coleta: municípios -> portal -> parser -> resultado."""

import logging
from datetime import date
from typing import Protocol

from ibge_coleta.exceptions import PortalError
from ibge_coleta.models import (
    DadosPortal,
    ErroColeta,
    Estado,
    Municipio,
    RegistroColeta,
    ResultadoColeta,
)

logger = logging.getLogger(__name__)


class FonteHTML(Protocol):
    """Qualquer objeto capaz de montar a URL de um município e devolver seu HTML."""

    def montar_url(self, municipio: Municipio) -> str: ...

    def obter_html(self, url: str) -> str: ...


class ParserCidade(Protocol):
    """Qualquer objeto capaz de converter o HTML do município em DadosPortal."""

    def extrair(self, html: str) -> DadosPortal: ...


class PipelineColeta:
    """Coleta os dados do portal para uma lista de municípios.

    Recebe a fonte de HTML e o parser por injeção de dependência, o que permite
    trocar o navegador real por uma implementação falsa nos testes.
    """

    def __init__(self, fonte: FonteHTML, parser: ParserCidade) -> None:
        self._fonte = fonte
        self._parser = parser

    def executar(self, estado: Estado, municipios: list[Municipio]) -> ResultadoColeta:
        resultado = ResultadoColeta(uf=estado.sigla, data_coleta=date.today())
        total = len(municipios)

        for posicao, municipio in enumerate(municipios, start=1):
            url = self._fonte.montar_url(municipio)
            logger.info("Coletando %s (%d/%d)", municipio.nome, posicao, total)
            try:
                html = self._fonte.obter_html(url)
            except PortalError as e:  # 404, redirecionamento, timeout, anti-bot...
                logger.warning("%s", e)
                resultado.erros.append(ErroColeta(municipio.nome, url, str(e)))
                continue

            dados = self._parser.extrair(html)
            resultado.registros.append(RegistroColeta(municipio, dados, url))

        logger.info(
            "UF %s: %d municípios processados, %d coletados, %d com falha",
            resultado.uf,
            total,
            len(resultado.registros),
            len(resultado.erros),
        )
        return resultado
