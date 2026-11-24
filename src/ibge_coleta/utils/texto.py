"""Funções utilitárias de tratamento de texto."""

import unicodedata


def remover_acentos(texto: str) -> str:
    """Remove acentos e cedilha: 'Água Preta' -> 'Agua Preta'."""
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def chave_ordenacao(texto: str) -> str:
    """Chave para ordenar nomes em português ignorando acentos e maiúsculas."""
    return remover_acentos(texto).casefold()
