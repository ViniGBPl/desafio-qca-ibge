"""Camada de aplicação: monta as dependências e expõe os casos de uso à interface."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path

from ibge_coleta.clients.ibge_api import IBGEAPIClient
from ibge_coleta.clients.portal import PortalPlaywright
from ibge_coleta.exporter import ExportadorExcel
from ibge_coleta.interfaces import Exportador, FonteHTML, FonteLocalidades, ParserCidade
from ibge_coleta.models import Estado, Municipio, ResultadoColeta
from ibge_coleta.parsers.cidade_parser import CidadeParser
from ibge_coleta.pipeline import PipelineColeta
from ibge_coleta.resumo import GeradorResumo

FabricaFonteHTML = Callable[[], AbstractContextManager[FonteHTML]]


class AplicacaoColeta:
    """Casos de uso: listar estados, listar municípios e coletar/exportar.

    Depende apenas de abstrações. A fonte de HTML é recebida como fábrica para que
    o navegador só seja aberto durante a coleta (e não enquanto o usuário usa o menu).
    """

    def __init__(
        self,
        localidades: FonteLocalidades,
        fabrica_fonte_html: FabricaFonteHTML,
        parser: ParserCidade,
        exportador: Exportador,
    ) -> None:
        self._localidades = localidades
        self._fabrica_fonte_html = fabrica_fonte_html
        self._parser = parser
        self._exportador = exportador

    def listar_estados(self) -> list[Estado]:
        return self._localidades.listar_estados()

    def listar_municipios(self, estado: Estado) -> list[Municipio]:
        return self._localidades.listar_municipios(estado)

    def coletar_e_exportar(
        self, estado: Estado, municipios: list[Municipio]
    ) -> tuple[ResultadoColeta, Path]:
        with self._fabrica_fonte_html() as fonte:
            resultado = PipelineColeta(fonte, self._parser).executar(estado, municipios)
        caminho = self._exportador.exportar(resultado)
        return resultado, caminho


def criar_aplicacao(api: IBGEAPIClient) -> AplicacaoColeta:
    """Raiz de composição: único ponto que conhece as implementações concretas."""
    return AplicacaoColeta(
        localidades=api,
        fabrica_fonte_html=PortalPlaywright,
        parser=CidadeParser(),
        exportador=ExportadorExcel(gerador_resumo=GeradorResumo()),
    )
