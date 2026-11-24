from datetime import date
from pathlib import Path

import pytest

from ibge_coleta.apresentacao.cli import exibir_resumo, interpretar_estado, interpretar_limite
from ibge_coleta.config import LIMITE_PADRAO
from ibge_coleta.dominio.models import Estado, ResultadoColeta

ESTADOS = [Estado("AC", "Acre", "Norte"), Estado("PE", "Pernambuco", "Nordeste")]


@pytest.mark.parametrize("entrada", ["2", "pe", "PE", "  pe  "])
def test_aceita_numero_ou_sigla(entrada):
    assert interpretar_estado(entrada, ESTADOS).sigla == "PE"


@pytest.mark.parametrize("entrada", ["0", "3", "-1", "xx", "", "1.5"])
def test_rejeita_estado_invalido(entrada):
    assert interpretar_estado(entrada, ESTADOS) is None


def test_limite_vazio_usa_o_padrao():
    assert interpretar_limite("", total=185) == LIMITE_PADRAO


def test_limite_padrao_nao_passa_do_total():
    assert interpretar_limite("", total=3) == 3


def test_limite_maior_que_o_total_usa_o_total():
    assert interpretar_limite("500", total=185) == 185


@pytest.mark.parametrize("entrada", ["0", "-2", "abc", "2.5"])
def test_rejeita_limite_invalido(entrada):
    assert interpretar_limite(entrada, total=185) is None


def test_resumo_no_terminal_mostra_avisos(capsys):
    resultado = ResultadoColeta(uf="PE", data_coleta=date(2026, 11, 24), total_processado=0)
    resultado.avisos.append("PIB não obtido na API de Agregados: Erro HTTP 500")

    exibir_resumo(resultado, Path("output/municipios_pe.xlsx"))

    saida = capsys.readouterr().out
    assert "Avisos:" in saida
    assert "PIB não obtido" in saida
