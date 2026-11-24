"""Camada de apresentação: menu de terminal para escolher a UF e o limite."""

from collections.abc import Callable
from pathlib import Path

from ibge_coleta.app import AplicacaoColeta
from ibge_coleta.config import LIMITE_PADRAO
from ibge_coleta.exceptions import ColetaError
from ibge_coleta.models import Estado, ResultadoColeta

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


def exibir_resumo(resultado: ResultadoColeta, caminho: Path) -> None:
    print(f"\nUF escolhida: {resultado.uf}")
    print(f"Municípios processados: {resultado.total_processado}")
    print(f"Coletados com sucesso: {len(resultado.registros)}")
    if resultado.erros:
        print("Falhas (URL não encontrada ou erro de acesso):")
        for erro in resultado.erros:
            print(f"  - {erro.municipio.nome} [{erro.municipio.codigo_ibge}]: {erro.motivo}")
    print(f"Planilha: {caminho}")


def executar_menu(app: AplicacaoColeta) -> int:
    """Conduz a interação com o usuário. Retorna o código de saída do programa."""
    try:
        estado = escolher_estado(app.listar_estados())
        municipios = app.listar_municipios(estado)
        selecionados = municipios[: escolher_limite(len(municipios))]
        resultado, caminho = app.coletar_e_exportar(estado, selecionados)
    except ColetaError as e:
        print(f"\nErro: {e}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nExecução cancelada pelo usuário.")
        return 130

    exibir_resumo(resultado, caminho)
    return 0
