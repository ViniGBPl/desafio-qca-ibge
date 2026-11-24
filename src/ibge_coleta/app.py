"""Camada de aplicação: casos de uso expostos à interface, dependendo só de abstrações."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path

from ibge_coleta.interfaces import (
    Exportador,
    FonteHTML,
    FonteIndicadorPIB,
    FonteLocalidades,
    ParserCidade,
)
from ibge_coleta.models import Estado, Municipio, ResultadoColeta
from ibge_coleta.pipeline import PipelineColeta

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
        fonte_pib: FonteIndicadorPIB | None = None,
    ) -> None:
        self._localidades = localidades
        self._fabrica_fonte_html = fabrica_fonte_html
        self._parser = parser
        self._exportador = exportador
        self._fonte_pib = fonte_pib

    def listar_estados(self) -> list[Estado]:
        return self._localidades.listar_estados()

    def listar_municipios(self, estado: Estado) -> list[Municipio]:
        return self._localidades.listar_municipios(estado)

    def coletar_e_exportar(
        self, estado: Estado, municipios: list[Municipio]
    ) -> tuple[ResultadoColeta, Path]:
        with self._fabrica_fonte_html() as fonte:
            pipeline = PipelineColeta(fonte, self._parser, self._fonte_pib)
            resultado = pipeline.executar(estado, municipios)
        caminho = self._exportador.exportar(resultado)
        return resultado, caminho
