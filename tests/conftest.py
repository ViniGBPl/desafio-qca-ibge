"""Fixtures compartilhadas pelos testes (sem rede e sem navegador)."""

from pathlib import Path

import pytest

from ibge_coleta.models import Estado, Municipio

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def html_recife() -> str:
    """HTML real da página de Recife, salvo com scripts/salvar_fixture.py."""
    return (FIXTURES / "recife.html").read_text(encoding="utf-8")


@pytest.fixture
def pernambuco() -> Estado:
    return Estado(sigla="PE", nome="Pernambuco", regiao="Nordeste")


@pytest.fixture
def criar_municipio():
    """Fábrica de municípios de PE para os testes."""

    def _criar(codigo: str, nome: str) -> Municipio:
        return Municipio(codigo_ibge=codigo, nome=nome, uf="PE", regiao="Nordeste")

    return _criar
