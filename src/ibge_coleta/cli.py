"""Menu de terminal: escolha da UF e do limite de municípios."""

from collections.abc import Callable

from ibge_coleta.clients.ibge_api import IBGEAPIClient
from ibge_coleta.config import LIMITE_PADRAO
from ibge_coleta.exceptions import ColetaError
from ibge_coleta.models import Estado, Municipio

LeitorEntrada = Callable[[str], str]


def interpretar_estado(entrada: str, estados: list[Estado]) -> Estado | None:
    """Aceita o número da lista (ex.: '17') ou a sigla (ex.: 'pe')."""
    entrada = entrada.strip()
    if entrada.isdigit():
        indice = int(entrada) - 1
        return estados[indice] if 0 <= indice < len(estados) else None

    sigla = entrada.upper()
    return next((e for e in estados if e.sigla == sigla), None)


def interpretar_limite(entrada: str, total: int) -> int | None:
    """Converte a quantidade digitada. Vazio usa o padrão; nunca passa do total."""
    entrada = entrada.strip()
    if not entrada:
        return min(LIMITE_PADRAO, total)
    if not entrada.isdigit() or int(entrada) == 0:
        return None
    return min(int(entrada), total)


def escolher_estado(estados: list[Estado], ler: LeitorEntrada = input) -> Estado:
    print("\nEstados disponíveis:")
    for numero, estado in enumerate(estados, start=1):
        print(f"  {numero:>2}) {estado.nome} ({estado.sigla})")

    while True:
        estado = interpretar_estado(ler("\nEscolha o número ou a sigla da UF: "), estados)
        if estado:
            return estado
        print(f"Opção inválida. Digite um número de 1 a {len(estados)} ou uma sigla (ex.: PE).")


def escolher_limite(total: int, ler: LeitorEntrada = input) -> int:
    while True:
        entrada = ler(f"Quantidade de municípios [{LIMITE_PADRAO}] (máx. {total}): ")
        limite = interpretar_limite(entrada, total)
        if limite is not None:
            if entrada.strip().isdigit() and int(entrada) > total:
                print(f"A UF tem apenas {total} municípios; usando {total}.")
            return limite
        print("Quantidade inválida. Digite um número inteiro maior que zero.")


def selecionar_municipios(api: IBGEAPIClient) -> tuple[Estado, list[Municipio]]:
    """Fluxo completo de seleção: UF -> municípios -> limite."""
    estado = escolher_estado(api.listar_estados())
    municipios = api.listar_municipios(estado)
    limite = escolher_limite(len(municipios))
    return estado, municipios[:limite]


def main() -> int:
    try:
        with IBGEAPIClient() as api:
            estado, municipios = selecionar_municipios(api)
    except ColetaError as e:
        print(f"\nErro: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nExecução cancelada pelo usuário.")
        return 130

    print(f"\nUF escolhida: {estado.nome} ({estado.sigla})")
    print(f"Municípios selecionados ({len(municipios)}):")
    for m in municipios:
        print(f"  - {m.nome} [{m.codigo_ibge}]")
    # Próximas etapas (portal, parser e exportação) entram aqui via pipeline.
    return 0
