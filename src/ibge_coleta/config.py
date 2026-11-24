"""Configurações centrais da aplicação."""

from pathlib import Path

API_BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
PORTAL_BASE_URL = "https://www.ibge.gov.br/cidades-e-estados"

# API de Agregados (SIDRA): tabela 5938 = PIB dos Municípios; variável 37 = PIB a preços
# correntes (Mil Reais). A tabela não tem PIB per capita, e calculá-lo misturaria o ano do
# PIB com o da população estimada, por isso o indicador é o PIB em si.
AGREGADOS_BASE_URL = "https://servicodados.ibge.gov.br/api/v3/agregados"
AGREGADO_PIB = 5938
VARIAVEL_PIB = 37

HTTP_TIMEOUT_S = 15.0
PAGE_TIMEOUT_MS = 60_000
PAUSA_ENTRE_PAGINAS_MS = 1_000

LIMITE_PADRAO = 5

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = RAIZ_PROJETO / "output"

# O portal fica atrás de verificação anti-bot (Cloudflare), que costuma barrar o modo headless.
PORTAL_HEADLESS = False
SELETOR_CONTEUDO = "div.indicador .ind-value"
