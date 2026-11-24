"""Testes do PortalPlaywright sem abrir navegador.

A página do Playwright é substituída por uma página falsa com os mesmos métodos
usados pelo portal (goto, wait_for_selector, title, url, content, wait_for_timeout).
"""

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ibge_coleta.config import PORTAL_BASE_URL
from ibge_coleta.dominio.exceptions import PaginaNaoEncontradaError, PortalError
from ibge_coleta.dominio.models import Municipio
from ibge_coleta.infraestrutura.clients.portal import PortalPlaywright

URL_RECIFE = f"{PORTAL_BASE_URL}/pe/recife.html"


class RespostaFake:
    def __init__(self, status: int) -> None:
        self.status = status


class PaginaFake:
    """Simula o comportamento da página real em cada cenário."""

    def __init__(
        self,
        status: int = 200,
        url_final: str | None = None,
        conteudo_carrega: bool = True,
        titulo: str = "Recife (PE) | Cidades e Estados | IBGE",
        goto_estoura_tempo: bool = False,
    ) -> None:
        self._status = status
        self._url_final = url_final
        self._conteudo_carrega = conteudo_carrega
        self._titulo = titulo
        self._goto_estoura_tempo = goto_estoura_tempo
        self.url = ""
        self.pausas = 0

    def goto(self, url, wait_until=None):
        if self._goto_estoura_tempo:
            raise PlaywrightTimeoutError("Timeout 60000ms exceeded")
        self.url = self._url_final or url
        return RespostaFake(self._status)

    def wait_for_selector(self, seletor):
        if not self._conteudo_carrega:
            raise PlaywrightTimeoutError("Timeout esperando o seletor")

    def title(self):
        return self._titulo

    def content(self):
        return "<html>conteúdo do município</html>"

    def wait_for_timeout(self, ms):
        self.pausas += 1


def criar_portal(pagina: PaginaFake) -> PortalPlaywright:
    portal = PortalPlaywright()
    portal._page = pagina  # simula o navegador já aberto, sem iniciar o Playwright
    return portal


@pytest.mark.parametrize(
    ("nome", "uf", "url_esperada"),
    [
        ("Recife", "PE", "pe/recife.html"),
        ("São José do Egito", "PE", "pe/sao-jose-do-egito.html"),
        ("Olho d'Água das Flores", "AL", "al/olho-dagua-das-flores.html"),
        ("Embu-Guaçu", "SP", "sp/embu-guacu.html"),
    ],
)
def test_monta_url_a_partir_da_uf_e_do_nome(nome, uf, url_esperada):
    municipio = Municipio(codigo_ibge="1", nome=nome, uf=uf, regiao="X")
    assert PortalPlaywright.montar_url(municipio) == f"{PORTAL_BASE_URL}/{url_esperada}"


def test_retorna_o_html_quando_a_pagina_carrega():
    pagina = PaginaFake()
    assert criar_portal(pagina).obter_html(URL_RECIFE) == "<html>conteúdo do município</html>"
    assert pagina.pausas == 1  # pausa de uso responsável entre páginas


def test_status_404_e_pagina_nao_encontrada():
    with pytest.raises(PaginaNaoEncontradaError, match="404"):
        criar_portal(PaginaFake(status=404)).obter_html(URL_RECIFE)


def test_outros_erros_http_sao_portal_error():
    with pytest.raises(PortalError, match="500") as erro:
        criar_portal(PaginaFake(status=500)).obter_html(URL_RECIFE)
    assert not isinstance(erro.value, PaginaNaoEncontradaError)


def test_redirecionamento_para_a_pagina_do_brasil_e_pagina_nao_encontrada():
    """URL inexistente redireciona para a página do Brasil, que tem os mesmos indicadores."""
    pagina = PaginaFake(url_final=f"{PORTAL_BASE_URL}.html")

    with pytest.raises(PaginaNaoEncontradaError, match="redirecionada"):
        criar_portal(pagina).obter_html(f"{PORTAL_BASE_URL}/pe/cidade-que-nao-existe.html")


def test_verificacao_anti_bot_com_403_que_se_resolve_retorna_o_html():
    """A Cloudflare responde 403 com a tela de verificação, que pode liberar a página."""
    pagina = PaginaFake(status=403, titulo="Just a moment...", conteudo_carrega=True)

    assert criar_portal(pagina).obter_html(URL_RECIFE) == "<html>conteúdo do município</html>"


def test_verificacao_anti_bot_com_403_que_nao_se_resolve_e_identificada():
    """Cenário observado em modo headless: 403 + tela de verificação até o timeout."""
    pagina = PaginaFake(status=403, titulo="Just a moment...", conteudo_carrega=False)

    with pytest.raises(PortalError, match="anti-bot"):
        criar_portal(pagina).obter_html(URL_RECIFE)


def test_403_sem_verificacao_anti_bot_e_erro_http():
    with pytest.raises(PortalError, match="Erro HTTP 403"):
        criar_portal(PaginaFake(status=403)).obter_html(URL_RECIFE)


def test_bloqueio_anti_bot_e_identificado():
    pagina = PaginaFake(conteudo_carrega=False, titulo="Just a moment...")

    with pytest.raises(PortalError, match="anti-bot"):
        criar_portal(pagina).obter_html(URL_RECIFE)


def test_pagina_sem_os_indicadores_e_pagina_nao_encontrada():
    with pytest.raises(PaginaNaoEncontradaError, match="Conteúdo"):
        criar_portal(PaginaFake(conteudo_carrega=False)).obter_html(URL_RECIFE)


def test_timeout_na_navegacao_vira_portal_error_e_ainda_pausa():
    pagina = PaginaFake(goto_estoura_tempo=True)

    with pytest.raises(PortalError, match="Tempo esgotado"):
        criar_portal(pagina).obter_html(URL_RECIFE)
    assert pagina.pausas == 1


def test_usar_sem_abrir_o_navegador_gera_erro_claro():
    with pytest.raises(PortalError, match="Navegador não iniciado"):
        PortalPlaywright().obter_html(URL_RECIFE)
