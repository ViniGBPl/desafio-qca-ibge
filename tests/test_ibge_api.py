import httpx
import pytest

from ibge_coleta.clients.ibge_api import IBGEAPIClient
from ibge_coleta.exceptions import IBGEAPIError
from ibge_coleta.models import Estado

PE = Estado("PE", "Pernambuco", "Nordeste")
UF_PE = {"sigla": "PE", "regiao": {"nome": "Nordeste"}}


def criar_cliente(handler) -> IBGEAPIClient:
    """Cliente com a rede simulada: nenhuma requisição real é feita."""
    return IBGEAPIClient(base_url="https://api.fake", transport=httpx.MockTransport(handler))


def test_lista_estados_ordenados_ignorando_acentos():
    estados = [
        {"sigla": "PI", "nome": "Piauí", "regiao": {"nome": "Nordeste"}},
        {"sigla": "AP", "nome": "Amapá", "regiao": {"nome": "Norte"}},
        {"sigla": "AL", "nome": "Alagoas", "regiao": {"nome": "Nordeste"}},
    ]
    with criar_cliente(lambda req: httpx.Response(200, json=estados)) as api:
        resultado = api.listar_estados()

    assert [e.sigla for e in resultado] == ["AL", "AP", "PI"]


def test_lista_municipios_com_e_sem_microrregiao():
    municipios = [
        {"id": 2611606, "nome": "Recife", "microrregiao": {"mesorregiao": {"UF": UF_PE}}},
        {
            "id": 2600401,
            "nome": "Água Preta",
            "microrregiao": None,
            "regiao-imediata": {"regiao-intermediaria": {"UF": UF_PE}},
        },
    ]
    with criar_cliente(lambda req: httpx.Response(200, json=municipios)) as api:
        resultado = api.listar_municipios(PE)

    assert [(m.codigo_ibge, m.nome, m.uf, m.regiao) for m in resultado] == [
        ("2600401", "Água Preta", "PE", "Nordeste"),
        ("2611606", "Recife", "PE", "Nordeste"),
    ]


def test_consulta_o_endpoint_da_uf_escolhida():
    caminhos = []

    def handler(req):
        caminhos.append(req.url.path)
        return httpx.Response(200, json=[{"id": 1, "nome": "X", "microrregiao": None}])

    with criar_cliente(handler) as api:
        api.listar_municipios(PE)

    assert caminhos == ["/estados/PE/municipios"]


@pytest.mark.parametrize(
    "resposta",
    [
        httpx.Response(500),
        httpx.Response(200, text="isso não é JSON"),
        httpx.Response(200, json={"erro": "esperava uma lista"}),
        httpx.Response(200, json=[]),
    ],
    ids=["http-500", "json-invalido", "formato-inesperado", "lista-vazia"],
)
def test_respostas_invalidas_viram_ibge_api_error(resposta):
    with criar_cliente(lambda req: resposta) as api, pytest.raises(IBGEAPIError):
        api.listar_municipios(PE)


def test_timeout_vira_ibge_api_error():
    def handler(req):
        raise httpx.ReadTimeout("demorou", request=req)

    with criar_cliente(handler) as api, pytest.raises(IBGEAPIError, match="Tempo esgotado"):
        api.listar_estados()
