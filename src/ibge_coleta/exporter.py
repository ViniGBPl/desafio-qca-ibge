"""Consolidação e exportação dos dados para Excel com pandas (Etapa D)."""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ibge_coleta.config import OUTPUT_DIR
from ibge_coleta.exceptions import ExportacaoError
from ibge_coleta.models import ResultadoColeta
from ibge_coleta.resumo import GeradorResumo, TabelasResumo
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
    # Diferencial: indicador da API de Agregados (após as 12 colunas obrigatórias)
    "pib_mil_reais",
    "ano_pib",
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
    "pib_mil_reais": "Float64",
    "ano_pib": "Int64",
}


ABA_DADOS = "municipios"
ABA_RESUMO = "resumo"
FORMATO_DATA = "DD/MM/YYYY"
LINHAS_ENTRE_SECOES = 2


class ExportadorExcel:
    """Grava a coleta em output/municipios_{uf}.xlsx, com as abas de dados e de resumo."""

    def __init__(
        self,
        pasta_saida: Path = OUTPUT_DIR,
        gerador_resumo: GeradorResumo | None = None,
    ) -> None:
        self._pasta_saida = pasta_saida
        self._gerador_resumo = gerador_resumo or GeradorResumo()

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
                "pib_mil_reais": r.pib.valor_mil_reais if r.pib else None,
                "ano_pib": r.pib.ano if r.pib else None,
            }
            for r in resultado.registros
        ]

        df = pd.DataFrame(linhas, columns=COLUNAS).astype(TIPOS)
        df = df.drop_duplicates(subset="codigo_ibge")
        df = df.sort_values("municipio", key=lambda col: col.map(chave_ordenacao))
        return df.reset_index(drop=True)

    def exportar(self, resultado: ResultadoColeta) -> Path:
        """Grava a planilha e devolve o caminho do arquivo gerado.

        Se o arquivo estiver bloqueado (ex.: aberto no Excel), salva uma cópia com data e
        hora no nome, para que a coleta não seja perdida.
        """
        df = self.montar_dataframe(resultado)
        caminho = self._pasta_saida / f"municipios_{resultado.uf.lower()}.xlsx"
        try:
            self._pasta_saida.mkdir(parents=True, exist_ok=True)
            self._gravar(df, resultado, caminho)
        except OSError as e:
            caminho = self._salvar_copia(df, resultado, caminho, e)

        logger.info("Planilha gerada: %s (%d linhas)", caminho, len(df))
        return caminho

    def _salvar_copia(
        self, df: pd.DataFrame, resultado: ResultadoColeta, original: Path, erro: OSError
    ) -> Path:
        copia = original.with_name(f"{original.stem}_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
        aviso = (
            f"Não foi possível gravar {original.name} (arquivo aberto em outro programa?); "
            f"a planilha foi salva como {copia.name}"
        )
        logger.warning("%s. Motivo: %s", aviso, erro)
        resultado.avisos.append(aviso)
        try:
            self._gravar(df, resultado, copia)
        except OSError as e:
            raise ExportacaoError(
                f"Não foi possível salvar a planilha em {original.parent}: {e}. "
                "Feche o arquivo se estiver aberto e execute novamente."
            ) from e
        return copia

    def _gravar(self, df: pd.DataFrame, resultado: ResultadoColeta, caminho: Path) -> None:
        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=ABA_DADOS, index=False)
            self._formatar_data(writer.sheets[ABA_DADOS], len(df))
            self._escrever_resumo(writer, self._gerador_resumo.gerar(resultado))

    @staticmethod
    def _formatar_data(planilha: Worksheet, total_linhas: int) -> None:
        """Exibe data_coleta só como data (sem 00:00:00)."""
        coluna = get_column_letter(COLUNAS.index("data_coleta") + 1)
        for linha in range(2, total_linhas + 2):
            planilha[f"{coluna}{linha}"].number_format = FORMATO_DATA

    @staticmethod
    def _escrever_resumo(writer: pd.ExcelWriter, tabelas: TabelasResumo) -> None:
        """Escreve as seções do resumo uma abaixo da outra, cada uma com título."""
        secoes = [
            ("Resumo da coleta", tabelas.indicadores, "Sem dados."),
            ("Municípios com falha", tabelas.erros, "Nenhuma falha."),
            ("Campos ausentes", tabelas.ausentes, "Nenhum campo ausente."),
            ("Avisos", tabelas.avisos, "Nenhum aviso."),
        ]
        linha = 0
        for titulo, tabela, mensagem_vazia in secoes:
            if tabela.empty:
                planilha = writer.sheets[ABA_RESUMO]
                planilha.cell(row=linha + 1, column=1, value=titulo).font = Font(bold=True)
                planilha.cell(row=linha + 2, column=1, value=mensagem_vazia)
                linha += 2 + LINHAS_ENTRE_SECOES
                continue

            tabela.to_excel(writer, sheet_name=ABA_RESUMO, startrow=linha + 1, index=False)
            planilha = writer.sheets[ABA_RESUMO]
            planilha.cell(row=linha + 1, column=1, value=titulo).font = Font(bold=True)
            linha += len(tabela) + 2 + LINHAS_ENTRE_SECOES
