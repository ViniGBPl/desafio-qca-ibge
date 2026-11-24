"""Acesso ao portal Cidades e Estados com Playwright (Etapa B)."""

import logging

from playwright.sync_api import Browser, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ibge_coleta.config import (
    PAGE_TIMEOUT_MS,
    PAUSA_ENTRE_PAGINAS_MS,
    PORTAL_BASE_URL,
    PORTAL_HEADLESS,
    SELETOR_CONTEUDO,
)
from ibge_coleta.dominio.exceptions import PaginaNaoEncontradaError, PortalError
from ibge_coleta.dominio.models import Municipio
from ibge_coleta.utils.texto import gerar_slug

logger = logging.getLogger(__name__)

TITULO_VERIFICACAO_ANTIBOT = "Just a moment"


class PortalPlaywright:
    """Navega pelas páginas dos municípios e devolve o HTML renderizado.

    Abre o navegador uma única vez e o reutiliza para todas as páginas.
    Use com 'with' para garantir que o navegador seja encerrado.
    """

    def __init__(
        self,
        headless: bool = PORTAL_HEADLESS,
        timeout_ms: int = PAGE_TIMEOUT_MS,
        pausa_ms: int = PAUSA_ENTRE_PAGINAS_MS,
    ) -> None:
        self._headless = headless
        self._timeout_ms = timeout_ms
        self._pausa_ms = pausa_ms
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    def __enter__(self) -> "PortalPlaywright":
        self.abrir()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.fechar()

    def abrir(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        self._page = self._browser.new_page()
        self._page.set_default_timeout(self._timeout_ms)

    def fechar(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._browser = self._playwright = self._page = None

    @staticmethod
    def montar_url(municipio: Municipio) -> str:
        """Ex.: Município 'São José do Egito' (PE) -> .../pe/sao-jose-do-egito.html"""
        return f"{PORTAL_BASE_URL}/{municipio.uf.lower()}/{gerar_slug(municipio.nome)}.html"

    def obter_html(self, url: str) -> str:
        """Abre a URL, aguarda o conteúdo relevante e devolve o HTML."""
        page = self._pagina()
        try:
            resposta = page.goto(url, wait_until="domcontentloaded")
            if resposta and resposta.status == 404:
                raise PaginaNaoEncontradaError(f"Página não encontrada (404): {url}")
            # A verificação anti-bot responde 403, mas pode se resolver sozinha em alguns
            # segundos; nesse caso a espera pelo conteúdo decide se a página liberou ou não.
            if resposta and resposta.status >= 400 and not self._em_verificacao_antibot(page):
                raise PortalError(f"Erro HTTP {resposta.status} ao acessar {url}")

            self._aguardar_conteudo(page, url)
            self._verificar_redirecionamento(page, url)
            return page.content()
        except PlaywrightTimeoutError as e:
            raise PortalError(f"Tempo esgotado ao carregar {url}") from e
        except PlaywrightError as e:
            raise PortalError(f"Falha do navegador ao acessar {url}: {e}") from e
        finally:
            self._pausar(page)

    def _pausar(self, page: Page) -> None:
        """Pausa entre páginas (uso responsável do portal); nunca deve mascarar o erro real."""
        try:
            page.wait_for_timeout(self._pausa_ms)
        except PlaywrightError:
            logger.debug("Não foi possível pausar: navegador indisponível")

    @staticmethod
    def _em_verificacao_antibot(page: Page) -> bool:
        return TITULO_VERIFICACAO_ANTIBOT in page.title()

    def _aguardar_conteudo(self, page: Page, url: str) -> None:
        try:
            page.wait_for_selector(SELETOR_CONTEUDO)
        except PlaywrightTimeoutError as e:
            if self._em_verificacao_antibot(page):
                raise PortalError(f"Verificação anti-bot não concluída em {url}") from e
            raise PaginaNaoEncontradaError(f"Conteúdo do município não encontrado em {url}") from e

    @staticmethod
    def _verificar_redirecionamento(page: Page, url: str) -> None:
        """O portal redireciona URLs inexistentes para a página do Brasil.

        Sem esta checagem, os dados do país seriam gravados como se fossem do município.
        """
        if page.url.rstrip("/") != url.rstrip("/"):
            raise PaginaNaoEncontradaError(
                f"URL não encontrada: {url} (redirecionada para {page.url})"
            )

    def _pagina(self) -> Page:
        if self._page is None:
            raise PortalError("Navegador não iniciado: use 'with PortalPlaywright() as portal'")
        return self._page
