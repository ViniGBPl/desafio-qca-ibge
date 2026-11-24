"""Consolidação e exportação dos dados para Excel com pandas (Etapa D)."""

import logging
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ibge_coleta.config import OUTPUT_DIR
from ibge_coleta.models import ResultadoColeta
from ibge_coleta.utils.texto import chave_ordenacao

logger = logging.getLogger(__name__)

COLUNAS = [
    "codigo_ibge",
    "municipio",
    "uf",
    "regiao",
    "prefeito",
    "gentilico",
    "populacao_estimada",
    "ano_populacao",
    "area_km2",
    "ano_area",
    "url_fonte",
    "data_coleta",
]

TIPOS = {
    "codigo_ibge": "string",
    "municipio": "string",
    "uf": "string",
    "regiao": "string",
    "prefeito": "string",
    "gentilico": "string",
    "populacao_estimada": "Int64",  # inteiro que aceita vazio
    "ano_populacao": "Int64",
    "area_km2": "Float64",
    "ano_area": "Int64",
    "url_fonte": "string",
}


ABA_DADOS = "municipios"
FORMATO_DATA = "DD/MM/YYYY"


class ExportadorExcel:
    """Monta o DataFrame da coleta e grava em output/municipios_{uf}.xlsx."""

    def __init__(self, pasta_saida: Path = OUTPUT_DIR) -> None:
        self._pasta_saida = pasta_saida

    def montar_dataframe(self, resultado: ResultadoColeta) -> pd.DataFrame:
        linhas = [
            {
                "codigo_ibge": r.municipio.codigo_ibge,
                "municipio": r.municipio.nome,
                "uf": r.municipio.uf,
                "regiao": r.municipio.regiao,
                "prefeito": r.dados.prefeito,
                "gentilico": r.dados.gentilico,
                "populacao_estimada": r.dados.populacao_estimada,
                "ano_populacao": r.dados.ano_populacao,
                "area_km2": r.dados.area_km2,
                "ano_area": r.dados.ano_area,
                "url_fonte": r.url_fonte,
                "data_coleta": resultado.data_coleta,
            }
            for r in resultado.registros
        ]

        df = pd.DataFrame(linhas, columns=COLUNAS).astype(TIPOS)
        df = df.drop_duplicates(subset="codigo_ibge")
        df = df.sort_values("municipio", key=lambda col: col.map(chave_ordenacao))
        return df.reset_index(drop=True)

    def exportar(self, resultado: ResultadoColeta) -> Path:
        df = self.montar_dataframe(resultado)
        self._pasta_saida.mkdir(parents=True, exist_ok=True)
        caminho = self._pasta_saida / f"municipios_{resultado.uf.lower()}.xlsx"

        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=ABA_DADOS, index=False)
            self._formatar_data(writer.sheets[ABA_DADOS], len(df))
        logger.info("Planilha gerada: %s (%d linhas)", caminho, len(df))
        return caminho

    @staticmethod
    def _formatar_data(planilha: Worksheet, total_linhas: int) -> None:
        """Exibe data_coleta só como data (sem 00:00:00)."""
        coluna = get_column_letter(COLUNAS.index("data_coleta") + 1)
        for linha in range(2, total_linhas + 2):
            planilha[f"{coluna}{linha}"].number_format = FORMATO_DATA
