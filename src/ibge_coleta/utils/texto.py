"""Funções utilitárias de tratamento de texto."""

import re
import unicodedata


def remover_acentos(texto: str) -> str:
    """Remove acentos e cedilha: 'Água Preta' -> 'Agua Preta'."""
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def chave_ordenacao(texto: str) -> str:
    """Chave para ordenar nomes em português ignorando acentos e maiúsculas."""
    return remover_acentos(texto).casefold()


def gerar_slug(nome: str) -> str:
    """Converte o nome do município no formato da URL do portal.

    'São José do Egito' -> 'sao-jose-do-egito'; "Olho d'Água" -> 'olho-dagua'.
    O apóstrofo é removido sem virar hífen.
    """
    sem_acento = remover_acentos(nome).lower().replace("'", "").replace("\u2019", "")
    return re.sub(r"[^a-z0-9]+", "-", sem_acento).strip("-")


def converter_inteiro_br(texto: str | None) -> int | None:
    """'1.588.983' -> 1588983. Retorna None se não for um número válido."""
    if not texto:
        return None
    limpo = texto.strip().replace(".", "")
    return int(limpo) if limpo.isdigit() else None


def converter_decimal_br(texto: str | None) -> float | None:
    """'218,843' -> 218.843 e '6.803,60' -> 6803.6. Retorna None se inválido."""
    if not texto:
        return None
    limpo = texto.strip().replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def extrair_ano(texto: str | None) -> int | None:
    """'[2025]' -> 2025."""
    if not texto:
        return None
    encontrado = re.search(r"\b(\d{4})\b", texto)
    return int(encontrado.group(1)) if encontrado else None
