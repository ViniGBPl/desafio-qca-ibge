import httpx
import pytest

from ibge_coleta.clients.agregados_api import AgregadosAPIClient
from ibge_coleta.exceptions import IBGEAPIError
from ibge_coleta.models import IndicadorPIB


def resposta_pib(series: dict[str, dict[str, str]]) -> list[dict]:
    """Monta uma resposta no formato real da API (confirmado na exploração)."""
    return [
        {
            "id": "37",
            "variavel": "Produto Interno Bruto a preços correntes",
            "unidade": "Mil Reais",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {"localidade": {"id": codigo, "nome": codigo}, "serie": serie}
                        for codigo, serie in series.items()
                    ],
                }
            ],
        }
    ]


def criar_cliente(handler) -> AgregadosAPIClient:
    return AgregadosAPIClient(base_url="https://api.fake", transport=httpx.MockTransport(handler))


def test_obtem_pib_de_varios_municipios_em_uma_requisicao():
    requisicoes = []

    def handler(req):
        requisicoes.append(req)
        series = {"2611606": {"2023": "66351305"}, "2609600": {"2023": "7024917"}}
        return httpx.Response(200, json=resposta_pib(series))

    with criar_cliente(handler) as api:
        pibs = api.obter_pib(["2611606", "2609600"])

    assert pibs == {
        "2611606": IndicadorPIB(valor_mil_reais=66351305.0, ano=2023),
        "2609600": IndicadorPIB(valor_mil_reais=7024917.0, ano=2023),
    }
    assert len(requisicoes) == 1
    assert requisicoes[0].url.path == "/5938/periodos/-1/variaveis/37"
    assert requisicoes[0].url.params["localidades"] == "N6[2611606,2609600]"


@pytest.mark.parametrize("simbolo", ["-", "...", "X"])
def test_valor_indisponivel_vira_none(simbolo):
    handler = lambda req: httpx.Response(200, json=resposta_pib({"1": {"2023": simbolo}}))  # noqa: E731

    with criar_cliente(handler) as api:
        assert api.obter_pib(["1"]) == {"1": IndicadorPIB(valor_mil_reais=None, ano=2023)}


def test_erro_no_lote_consulta_um_a_um_e_mantem_os_validos():
    """A API devolve 500 para o lote inteiro se um código não existir na série."""

    def handler(req):
        if "9999999" in req.url.params["localidades"]:
            return httpx.Response(500, json={"message": "Internal server error"})
        return httpx.Response(200, json=resposta_pib({"2611606": {"2023": "66351305"}}))

    with criar_cliente(handler) as api:
        pibs = api.obter_pib(["2611606", "9999999"])

    assert pibs == {"2611606": IndicadorPIB(valor_mil_reais=66351305.0, ano=2023)}


def test_falha_com_um_unico_municipio_propaga_o_erro():
    with criar_cliente(lambda req: httpx.Response(500)) as api, pytest.raises(IBGEAPIError):
        api.obter_pib(["2611606"])


def test_lista_vazia_nao_faz_requisicao():
    def handler(req):
        raise AssertionError("não deveria chamar a API")

    with criar_cliente(handler) as api:
        assert api.obter_pib([]) == {}


def test_json_malformado_vira_ibge_api_error():
    json_sem_localidade = [{"resultados": [{"series": [{"serie": {"2023": "1"}}]}]}]
    handler = lambda req: httpx.Response(200, json=json_sem_localidade)  # noqa: E731

    with criar_cliente(handler) as api, pytest.raises(IBGEAPIError, match="Formato inesperado"):
        api.obter_pib(["2611606"])


def test_json_malformado_em_lote_nao_derruba_o_programa():
    json_sem_localidade = [{"resultados": [{"series": [{"serie": {"2023": "1"}}]}]}]
    handler = lambda req: httpx.Response(200, json=json_sem_localidade)  # noqa: E731

    with criar_cliente(handler) as api:
        assert api.obter_pib(["2611606", "2609600"]) == {}
