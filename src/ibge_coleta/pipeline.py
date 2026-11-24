"""Orquestra a coleta: municípios -> portal -> parser -> resultado."""

import logging
from datetime import date

from ibge_coleta.exceptions import ColetaError, PortalError
from ibge_coleta.interfaces import FonteHTML, FonteIndicadorPIB, ParserCidade
from ibge_coleta.models import ErroColeta, Estado, Municipio, RegistroColeta, ResultadoColeta

logger = logging.getLogger(__name__)


class PipelineColeta:
    """Coleta os dados do portal para uma lista de municípios.

    Recebe a fonte de HTML, o parser e (opcionalmente) a fonte do PIB por injeção de
    dependência, o que permite trocar as implementações reais por falsas nos testes.
    """

    def __init__(
        self,
        fonte: FonteHTML,
        parser: ParserCidade,
        fonte_pib: FonteIndicadorPIB | None = None,
    ) -> None:
        self._fonte = fonte
        self._parser = parser
        self._fonte_pib = fonte_pib

    def executar(self, estado: Estado, municipios: list[Municipio]) -> ResultadoColeta:
        resultado = ResultadoColeta(
            uf=estado.sigla, data_coleta=date.today(), total_processado=len(municipios)
        )

        for posicao, municipio in enumerate(municipios, start=1):
            url = self._fonte.montar_url(municipio)
            logger.info("Coletando %s (%d/%d)", municipio.nome, posicao, len(municipios))
            try:
                html = self._fonte.obter_html(url)
            except PortalError as e:  # 404, redirecionamento, timeout, anti-bot...
                logger.warning("%s: %s", municipio.nome, e)
                resultado.erros.append(ErroColeta(municipio, url, str(e)))
                continue

            dados = self._parser.extrair(html)
            if ausentes := dados.campos_ausentes():
                logger.warning("%s: campos ausentes na página: %s", municipio.nome, ausentes)
            resultado.registros.append(RegistroColeta(municipio, dados, url))

        self._adicionar_pib(resultado)
        logger.info(
            "UF %s: %d municípios processados, %d coletados, %d com falha",
            resultado.uf,
            resultado.total_processado,
            len(resultado.registros),
            len(resultado.erros),
        )
        return resultado

    def _adicionar_pib(self, resultado: ResultadoColeta) -> None:
        """Enriquece os registros com o PIB. Uma falha aqui não invalida a coleta principal."""
        if self._fonte_pib is None or not resultado.registros:
            return

        codigos = [r.municipio.codigo_ibge for r in resultado.registros]
        try:
            pibs = self._fonte_pib.obter_pib(codigos)
        except ColetaError as e:
            aviso = f"PIB não obtido na API de Agregados: {e}"
            logger.warning(aviso)
            resultado.avisos.append(aviso)
            return

        for registro in resultado.registros:
            registro.pib = pibs.get(registro.municipio.codigo_ibge)
