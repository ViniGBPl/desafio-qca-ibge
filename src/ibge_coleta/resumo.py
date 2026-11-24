"""Montagem do resumo da coleta (UF, totais, erros e dados ausentes)."""

from dataclasses import dataclass

import pandas as pd

from ibge_coleta.models import ResultadoColeta


@dataclass(frozen=True)
class TabelasResumo:
    """As três tabelas que compõem a aba de resumo."""

    indicadores: pd.DataFrame
    erros: pd.DataFrame
    ausentes: pd.DataFrame


class GeradorResumo:
    """Transforma o ResultadoColeta em tabelas de resumo.

    Não sabe nada de Excel: só monta DataFrames. Quem decide onde e como
    gravar é o exportador.
    """

    def gerar(self, resultado: ResultadoColeta) -> TabelasResumo:
        return TabelasResumo(
            indicadores=self._indicadores(resultado),
            erros=self._erros(resultado),
            ausentes=self._ausentes(resultado),
        )

    @staticmethod
    def _indicadores(resultado: ResultadoColeta) -> pd.DataFrame:
        # Conta por código IBGE para ficar coerente com a aba de dados, que remove duplicados.
        coletados = {r.municipio.codigo_ibge for r in resultado.registros}
        com_ausentes = {
            r.municipio.codigo_ibge for r in resultado.registros if r.dados.campos_ausentes()
        }
        linhas = [
            ("UF selecionada", resultado.uf),
            ("Data da coleta", resultado.data_coleta.strftime("%d/%m/%Y")),
            ("Municípios processados", resultado.total_processado),
            ("Coletados com sucesso", len(coletados)),
            ("Com falha (URL não encontrada ou erro)", len(resultado.erros)),
            ("Coletados com campos ausentes", len(com_ausentes)),
        ]
        return pd.DataFrame(linhas, columns=["indicador", "valor"])

    @staticmethod
    def _erros(resultado: ResultadoColeta) -> pd.DataFrame:
        linhas = [
            {
                "codigo_ibge": e.municipio.codigo_ibge,
                "municipio": e.municipio.nome,
                "url": e.url,
                "motivo": e.motivo,
            }
            for e in resultado.erros
        ]
        return pd.DataFrame(linhas, columns=["codigo_ibge", "municipio", "url", "motivo"])

    @staticmethod
    def _ausentes(resultado: ResultadoColeta) -> pd.DataFrame:
        linhas = [
            {
                "codigo_ibge": r.municipio.codigo_ibge,
                "municipio": r.municipio.nome,
                "campos_ausentes": ", ".join(ausentes),
            }
            for r in resultado.registros
            if (ausentes := r.dados.campos_ausentes())
        ]
        return pd.DataFrame(linhas, columns=["codigo_ibge", "municipio", "campos_ausentes"])
