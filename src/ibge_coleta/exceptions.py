"""Exceções da aplicação."""


class ColetaError(Exception):
    """Erro base da coleta."""


class IBGEAPIError(ColetaError):
    """Falha ao consultar a API do IBGE."""


class PortalError(ColetaError):
    """Falha ao acessar o portal Cidades e Estados."""


class PaginaNaoEncontradaError(PortalError):
    """A página do município não existe no portal."""
