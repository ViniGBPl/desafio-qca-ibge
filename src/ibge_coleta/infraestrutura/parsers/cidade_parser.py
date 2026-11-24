"""Extração dos dados do município a partir do HTML do portal (Etapa C)."""

from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString, Tag

from ibge_coleta.dominio.models import DadosPortal
from ibge_coleta.utils.texto import converter_decimal_br, converter_inteiro_br, extrair_ano


@dataclass(frozen=True)
class Indicador:
    """Um bloco 'div.indicador' do portal: rótulo, valor e ano de referência."""

    rotulo: str
    valor: str
    ano: int | None


class CidadeParser:
    """Converte o HTML da página do município em DadosPortal.

    Todos os blocos 'div.indicador' são lidos para um dicionário rótulo -> Indicador,
    e cada campo é buscado pelo rótulo exato (não pela posição na página). Assim, a
    leitura do HTML é genérica; um campo novo exige só o rótulo, o atributo em
    DadosPortal e a coluna no exportador. Campos ausentes ficam como None.
    """

    ROTULO_PREFEITO = "Prefeito"
    ROTULO_GENTILICO = "Gentílico"
    ROTULO_POPULACAO = "População estimada"
    ROTULO_AREA = "Área Territorial"

    def extrair(self, html: str) -> DadosPortal:
        indicadores = self._mapear_indicadores(html)

        prefeito = indicadores.get(self.ROTULO_PREFEITO)
        gentilico = indicadores.get(self.ROTULO_GENTILICO)
        populacao = indicadores.get(self.ROTULO_POPULACAO)
        area = indicadores.get(self.ROTULO_AREA)

        return DadosPortal(
            prefeito=prefeito.valor if prefeito else None,
            gentilico=gentilico.valor if gentilico else None,
            populacao_estimada=converter_inteiro_br(populacao.valor) if populacao else None,
            ano_populacao=populacao.ano if populacao else None,
            area_km2=converter_decimal_br(area.valor) if area else None,
            ano_area=area.ano if area else None,
        )

    def _mapear_indicadores(self, html: str) -> dict[str, Indicador]:
        soup = BeautifulSoup(html, "html.parser")
        indicadores: dict[str, Indicador] = {}

        for bloco in soup.select("div.indicador"):
            rotulo_tag = bloco.select_one(".ind-label p")
            valor_tag = bloco.select_one(".ind-value")
            if not rotulo_tag or not valor_tag:
                continue

            rotulo = rotulo_tag.get_text(strip=True)
            ano_tag = valor_tag.find("small")
            indicadores[rotulo] = Indicador(
                rotulo=rotulo,
                valor=self._texto_direto(valor_tag),
                ano=extrair_ano(ano_tag.get_text()) if ano_tag else None,
            )
        return indicadores

    @staticmethod
    def _texto_direto(tag: Tag) -> str:
        """Texto do próprio elemento, sem a unidade (<span>) e o ano (<small>)."""
        partes = [str(filho) for filho in tag.children if isinstance(filho, NavigableString)]
        return " ".join("".join(partes).split())
