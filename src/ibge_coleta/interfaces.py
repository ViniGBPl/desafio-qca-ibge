"""Abstrações (Protocols) que desacoplam as camadas das implementações concretas.

Qualquer classe que tenha os mesmos métodos satisfaz o contrato, sem herança
(duck typing tipado). Isso permite trocar implementações reais por falsas nos testes.
"""

from pathlib import Path
from typing import Protocol

from ibge_coleta.models import DadosPortal, Estado, Municipio, ResultadoColeta


class FonteLocalidades(Protocol):
    """Fornece estados e municípios (ex.: API de Localidades do IBGE)."""

    def listar_estados(self) -> list[Estado]: ...

    def listar_municipios(self, estado: Estado) -> list[Municipio]: ...


class FonteHTML(Protocol):
    """Monta a URL de um município e devolve o HTML da página."""

    def montar_url(self, municipio: Municipio) -> str: ...

    def obter_html(self, url: str) -> str: ...


class ParserCidade(Protocol):
    """Converte o HTML da página do município em DadosPortal."""

    def extrair(self, html: str) -> DadosPortal: ...


class Exportador(Protocol):
    """Grava o resultado da coleta e devolve o caminho do arquivo gerado."""

    def exportar(self, resultado: ResultadoColeta) -> Path: ...
