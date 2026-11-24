"""Modelos de dados compartilhados entre as camadas."""

from dataclasses import dataclass, field, fields
from datetime import date


@dataclass(frozen=True)
class Estado:
    sigla: str
    nome: str
    regiao: str


@dataclass(frozen=True)
class Municipio:
    codigo_ibge: str
    nome: str
    uf: str
    regiao: str


@dataclass
class DadosPortal:
    prefeito: str | None = None
    gentilico: str | None = None
    populacao_estimada: int | None = None
    ano_populacao: int | None = None
    area_km2: float | None = None
    ano_area: int | None = None

    def campos_ausentes(self) -> list[str]:
        """Nomes dos campos que não foram encontrados na página."""
        return [f.name for f in fields(self) if getattr(self, f.name) in (None, "")]


@dataclass
class RegistroColeta:
    municipio: Municipio
    dados: DadosPortal
    url_fonte: str


@dataclass
class ErroColeta:
    municipio: Municipio
    url: str
    motivo: str


@dataclass
class ResultadoColeta:
    uf: str
    data_coleta: date
    total_processado: int = 0
    registros: list[RegistroColeta] = field(default_factory=list)
    erros: list[ErroColeta] = field(default_factory=list)
