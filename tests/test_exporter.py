from datetime import date

import openpyxl
import pytest

from ibge_coleta.exporter import COLUNAS, ExportadorExcel
from ibge_coleta.models import (
    DadosPortal,
    ErroColeta,
    IndicadorPIB,
    RegistroColeta,
    ResultadoColeta,
)

DADOS_COMPLETOS = DadosPortal("PREFEITO", "gentilico", 1588983, 2026, 218.843, 2025)


@pytest.fixture
def resultado(criar_municipio) -> ResultadoColeta:
    recife = criar_municipio("2611606", "Recife")
    return ResultadoColeta(
        uf="PE",
        data_coleta=date(2026, 11, 24),
        total_processado=4,
        registros=[
            RegistroColeta(recife, DADOS_COMPLETOS, "url-recife", IndicadorPIB(66351305.0, 2023)),
            RegistroColeta(criar_municipio("2600401", "Água Preta"), DadosPortal(), "url-ap"),
            RegistroColeta(recife, DADOS_COMPLETOS, "url-recife"),  # duplicado
        ],
        erros=[ErroColeta(criar_municipio("1", "Inexistente"), "url-x", "URL não encontrada")],
    )


def test_dataframe_tem_as_colunas_na_ordem_do_enunciado(resultado):
    df = ExportadorExcel().montar_dataframe(resultado)
    assert list(df.columns) == COLUNAS
    assert COLUNAS[:12] == [
        "codigo_ibge",
        "municipio",
        "uf",
        "regiao",
        "prefeito",
        "gentilico",
        "populacao_estimada",
        "ano_populacao",
        "area_km2",
        "ano_area",
        "url_fonte",
        "data_coleta",
    ]  # as 12 obrigatórias vêm primeiro; o PIB (diferencial) fica depois


def test_colunas_do_pib(resultado):
    df = ExportadorExcel().montar_dataframe(resultado)
    recife = df[df["municipio"] == "Recife"].iloc[0]
    agua_preta = df[df["municipio"] == "Água Preta"].iloc[0]

    assert recife["pib_mil_reais"] == pytest.approx(66351305.0)
    assert recife["ano_pib"] == 2023
    assert agua_preta[["pib_mil_reais", "ano_pib"]].isna().all()


def test_remove_duplicados_e_ordena_ignorando_acentos(resultado):
    df = ExportadorExcel().montar_dataframe(resultado)
    assert list(df["municipio"]) == ["Água Preta", "Recife"]


def test_tipos_e_campos_ausentes_ficam_vazios(resultado):
    df = ExportadorExcel().montar_dataframe(resultado)
    recife = df[df["municipio"] == "Recife"].iloc[0]
    agua_preta = df[df["municipio"] == "Água Preta"].iloc[0]

    assert recife["codigo_ibge"] == "2611606"
    assert recife["populacao_estimada"] == 1588983
    assert recife["area_km2"] == pytest.approx(218.843)
    assert str(df["populacao_estimada"].dtype) == "Int64"
    assert agua_preta[["prefeito", "populacao_estimada", "area_km2"]].isna().all()


def test_gera_arquivo_com_nome_da_uf_e_aba_de_resumo(resultado, tmp_path):
    caminho = ExportadorExcel(pasta_saida=tmp_path).exportar(resultado)

    assert caminho.name == "municipios_pe.xlsx"
    planilha = openpyxl.load_workbook(caminho)
    assert planilha.sheetnames == ["municipios", "resumo"]

    resumo = [linha[:2] for linha in planilha["resumo"].iter_rows(values_only=True)]
    assert ("UF selecionada", "PE") in resumo
    assert ("Municípios processados", 4) in resumo
    assert ("Coletados com sucesso", 2) in resumo  # o duplicado não é contado duas vezes
    assert ("Com PIB obtido (API de Agregados)", 1) in resumo
    assert any(linha[1] == "Inexistente" for linha in resumo)
    assert any(linha[1] == "Água Preta" for linha in resumo)
