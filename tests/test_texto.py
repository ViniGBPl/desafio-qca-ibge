import pytest

from ibge_coleta.utils.texto import (
    chave_ordenacao,
    converter_decimal_br,
    converter_inteiro_br,
    extrair_ano,
    gerar_slug,
)


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("Recife", "recife"),
        ("São José do Egito", "sao-jose-do-egito"),
        ("Olho d'Água das Flores", "olho-dagua-das-flores"),
        ("Embu-Guaçu", "embu-guacu"),
        ("Água Preta", "agua-preta"),
    ],
)
def test_gerar_slug(nome, esperado):
    assert gerar_slug(nome) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("1.588.983", 1588983), ("32523", 32523), ("", None), (None, None), ("abc", None)],
)
def test_converter_inteiro_br(texto, esperado):
    assert converter_inteiro_br(texto) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("218,843", 218.843), ("6.803,60", 6803.6), ("774,037", 774.037), ("", None), ("x", None)],
)
def test_converter_decimal_br(texto, esperado):
    assert converter_decimal_br(texto) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"), [("[2025]", 2025), (" [2026] ", 2026), ("sem ano", None), (None, None)]
)
def test_extrair_ano(texto, esperado):
    assert extrair_ano(texto) == esperado


def test_ordenacao_ignora_acentos():
    nomes = ["Alagoinha", "Água Preta", "Agrestina", "Afrânio"]
    assert sorted(nomes, key=chave_ordenacao) == ["Afrânio", "Agrestina", "Água Preta", "Alagoinha"]
