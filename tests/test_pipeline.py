from ibge_coleta.exceptions import PaginaNaoEncontradaError, PortalError
from ibge_coleta.parsers.cidade_parser import CidadeParser
from ibge_coleta.pipeline import PipelineColeta


class PortalFake:
    """Implementa o contrato FonteHTML sem abrir navegador."""

    def __init__(self, paginas: dict[str, str | Exception]) -> None:
        self._paginas = paginas
        self.urls_visitadas: list[str] = []

    def montar_url(self, municipio):
        return f"https://portal.fake/{municipio.nome}"

    def obter_html(self, url):
        self.urls_visitadas.append(url)
        resposta = self._paginas[url.rsplit("/", 1)[-1]]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def test_coleta_todos_os_municipios(pernambuco, html_recife, criar_municipio):
    portal = PortalFake({"Recife": html_recife, "Olinda": html_recife})
    municipios = [criar_municipio("2611606", "Recife"), criar_municipio("2609600", "Olinda")]

    resultado = PipelineColeta(portal, CidadeParser()).executar(pernambuco, municipios)

    assert resultado.uf == "PE"
    assert resultado.total_processado == 2
    assert len(resultado.registros) == 2
    assert resultado.erros == []


def test_falha_em_um_municipio_nao_interrompe_os_demais(pernambuco, html_recife, criar_municipio):
    portal = PortalFake(
        {
            "Inexistente": PaginaNaoEncontradaError("URL não encontrada"),
            "Lenta": PortalError("Tempo esgotado"),
            "Recife": html_recife,
        }
    )
    municipios = [
        criar_municipio("1", "Inexistente"),
        criar_municipio("2", "Lenta"),
        criar_municipio("2611606", "Recife"),
    ]

    resultado = PipelineColeta(portal, CidadeParser()).executar(pernambuco, municipios)

    assert len(portal.urls_visitadas) == 3
    assert [r.municipio.nome for r in resultado.registros] == ["Recife"]
    assert [(e.municipio.codigo_ibge, e.motivo) for e in resultado.erros] == [
        ("1", "URL não encontrada"),
        ("2", "Tempo esgotado"),
    ]


def test_registro_guarda_a_url_consultada(pernambuco, html_recife, criar_municipio):
    portal = PortalFake({"Recife": html_recife})

    resultado = PipelineColeta(portal, CidadeParser()).executar(
        pernambuco, [criar_municipio("2611606", "Recife")]
    )

    assert resultado.registros[0].url_fonte == "https://portal.fake/Recife"
