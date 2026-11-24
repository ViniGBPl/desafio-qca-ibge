from ibge_coleta.dominio.models import DadosPortal
from ibge_coleta.infraestrutura.parsers.cidade_parser import CidadeParser


def test_extrai_todos_os_campos_do_html_real(html_recife):
    dados = CidadeParser().extrair(html_recife)

    assert dados == DadosPortal(
        prefeito="JOÃO HENRIQUE DE ANDRADE LIMA CAMPOS",
        gentilico="recifense",
        populacao_estimada=1588983,
        ano_populacao=2026,
        area_km2=218.843,
        ano_area=2025,
    )


def test_usa_populacao_estimada_e_nao_a_do_censo(html_recife):
    """A página também tem 'População no último censo' (1.488.920 [2022])."""
    dados = CidadeParser().extrair(html_recife)

    assert dados.populacao_estimada != 1488920
    assert dados.ano_populacao != 2022


def test_html_sem_indicadores_retorna_campos_vazios():
    dados = CidadeParser().extrair("<html><body><p>Página sem dados</p></body></html>")

    assert dados == DadosPortal()
    assert len(dados.campos_ausentes()) == 6


def test_campo_ausente_fica_vazio_e_os_demais_sao_extraidos():
    html = """
    <div class="indicador">
      <div class="ind-label"><p>Gentílico</p></div>
      <p class="ind-value">recifense</p>
    </div>
    """
    dados = CidadeParser().extrair(html)

    assert dados.gentilico == "recifense"
    assert dados.prefeito is None
    assert "prefeito" in dados.campos_ausentes()
