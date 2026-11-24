import pytest

from ibge_coleta.cli import interpretar_estado, interpretar_limite
from ibge_coleta.config import LIMITE_PADRAO
from ibge_coleta.models import Estado

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
