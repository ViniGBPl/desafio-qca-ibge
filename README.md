# Desafio Técnico QCA — Coleta de dados de municípios do IBGE

Aplicação em Python que lista os estados brasileiros pela **API de Localidades do IBGE**, deixa o usuário escolher uma UF, visita a página de cada município no portal **Cidades e Estados** e gera uma planilha Excel com os dados coletados.

```
listar estados (API) → escolher UF → consultar municípios (API) → coletar no portal (Playwright) → extrair (BeautifulSoup) → exportar Excel (pandas)
```

| Biblioteca | Uso no projeto |
|---|---|
| **httpx** | Consulta à API REST de Localidades (estados e municípios) |
| **Playwright** | Navegação real nas páginas dos municípios no portal |
| **BeautifulSoup4** | Extração dos dados do HTML obtido pelo Playwright |
| **pandas** | Limpeza, tipagem e exportação para Excel |

---

## Requisitos

- Python **3.11 ou superior**
- Conexão com a internet
- Ambiente com interface gráfica (o navegador abre visível — ver [Limitações](#limitações-conhecidas))

## Instalação

```bash
git clone https://github.com/ViniGBPl/desafio-qca-ibge.git
cd desafio-qca-ibge

python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

> O comando `playwright install chromium` é obrigatório: ele baixa o navegador usado na coleta.

Para desenvolvimento (testes e lint): `pip install -r requirements-dev.txt`.

## Como executar

```bash
python main.py
```

O programa mostra a lista numerada de estados (obtida da API) e pede duas informações:

```
Estados disponíveis:
   1) Acre (AC)
   ...
  17) Pernambuco (PE)
   ...

Escolha o número ou a sigla da UF: pe
Quantidade de municípios [5] (máx. 185):
```

**Escolhendo o estado:** digite o **número** da lista (ex.: `17`) ou a **sigla** (ex.: `pe`, sem diferenciar maiúsculas). Entradas inválidas mostram uma mensagem e o programa pergunta de novo.

**Ajustando o limite de municípios:**
- Pressione **Enter** para usar o padrão de **5 municípios**.
- Digite outro número para alterar o limite (ex.: `20`).
- Se o número for maior que o total de municípios da UF, o programa avisa e usa o total — nunca extrapola o que a API retornou.
- Os municípios são ordenados por nome e o programa processa os primeiros N.

Ao final, é exibido um resumo (UF escolhida, quantidade processada, coletados com sucesso e falhas com o motivo) e a planilha é gerada em:

```
output/municipios_{uf}.xlsx      (ex.: output/municipios_pe.xlsx)
```

## Estrutura da planilha

Uma linha por município, ordenada por nome, sem duplicados (chave: `codigo_ibge`).

| Coluna | Tipo | Origem |
|---|---|---|
| `codigo_ibge` | Texto (7 dígitos) | API |
| `municipio` | Texto | API |
| `uf` | Texto | API |
| `regiao` | Texto | API |
| `prefeito` | Texto ou vazio | Portal |
| `gentilico` | Texto ou vazio | Portal |
| `populacao_estimada` | Inteiro | Portal |
| `ano_populacao` | Inteiro | Portal |
| `area_km2` | Decimal | Portal |
| `ano_area` | Inteiro | Portal |
| `url_fonte` | URL consultada | Gerada a partir da UF e do nome |
| `data_coleta` | Data (DD/MM/AAAA) | Data da execução |

Números no formato brasileiro (`1.588.983`, `218,843`) são convertidos para tipos numéricos, e os anos de referência ficam em colunas separadas dos valores. **Dados ausentes ficam vazios** — nenhum valor é inventado ou preenchido com zero.

### Aba `resumo`

A planilha tem uma segunda aba que registra a execução, para que essas informações não fiquem só no terminal:

- **Resumo da coleta:** UF selecionada, data, municípios processados, coletados com sucesso, quantidade com falha e quantidade com campos ausentes.
- **Municípios com falha:** código IBGE, nome, URL tentada e motivo (URL não encontrada, timeout, bloqueio...).
- **Campos ausentes:** municípios coletados em que algum campo não foi encontrado na página, e quais campos.

---

## Arquitetura

O projeto segue uma **arquitetura em camadas**: cada camada só depende das camadas abaixo dela e conversa com as outras por contratos (`Protocol`) e modelos de dados comuns.

```
main.py                      Ponto de entrada
└── cli.py                   APRESENTAÇÃO   menu de terminal (input/print)
    └── app.py               APLICAÇÃO      casos de uso + montagem das dependências
        ├── pipeline.py      SERVIÇO        orquestra portal → parser por município
        ├── exporter.py      SERVIÇO        DataFrame e Excel
        ├── resumo.py        SERVIÇO        tabelas da aba de resumo
        ├── parsers/         SERVIÇO        HTML → dados (BeautifulSoup)
        └── clients/         INFRAESTRUTURA API (httpx) e portal (Playwright)

interfaces.py   contratos entre as camadas (Protocols)
models.py       dataclasses compartilhadas (Estado, Municipio, DadosPortal...)
exceptions.py   hierarquia de erros da aplicação
config.py       URLs, timeouts e limite padrão
utils/texto.py  slug de URL, conversão de números e ordenação sem acento
```

```
desafio-qca-ibge/
├── main.py
├── src/ibge_coleta/
│   ├── cli.py, app.py, pipeline.py, exporter.py, resumo.py
│   ├── interfaces.py, models.py, exceptions.py, config.py
│   ├── clients/   ibge_api.py, portal.py
│   ├── parsers/   cidade_parser.py
│   └── utils/     texto.py
├── scripts/salvar_fixture.py   salva o HTML de uma página para testes
├── tests/                      testes automatizados (pytest)
│   └── fixtures/recife.html    HTML real do portal, usado para testar o parser
├── output/                     planilha gerada
├── requirements.txt, requirements-dev.txt, pyproject.toml
```

### Princípios aplicados

**SOLID**, de forma pragmática (sem criar abstrações onde só existe uma implementação):

- **S — Responsabilidade única:** cada classe tem um papel: `IBGEAPIClient` só fala com a API, `PortalPlaywright` só navega, `CidadeParser` só interpreta HTML, `ExportadorExcel` só grava a planilha, `GeradorResumo` só monta as tabelas do resumo, `PipelineColeta` só orquestra.
- **O — Aberto/fechado:** o parser lê todos os indicadores da página de forma genérica e busca cada campo pelo rótulo; extrair um campo novo não exige mudar a lógica de leitura do HTML.
- **L / I — Substituição e interfaces enxutas:** os contratos em `interfaces.py` têm só os métodos necessários (`FonteHTML` tem 2, `ParserCidade` tem 1), e qualquer implementação que os cumpra pode ser usada no lugar da real.
- **D — Inversão de dependência:** `PipelineColeta` e `AplicacaoColeta` recebem suas dependências pelo construtor e dependem de abstrações, não de Playwright ou httpx. O único lugar que conhece as classes concretas é `criar_aplicacao()` (raiz de composição).

**POO:**

- **Encapsulamento:** detalhes internos ficam em atributos e métodos privados (`_client`, `_page`, `_aguardar_conteudo`); quem usa as classes só vê métodos como `listar_municipios()` e `obter_html()`.
- **Abstração:** o pipeline pede "o HTML deste município" sem saber que existe um navegador.
- **Herança:** hierarquia de exceções `ColetaError` → `PortalError` → `PaginaNaoEncontradaError`, permitindo tratar erros no nível certo de detalhe.
- **Polimorfismo:** o pipeline funciona igual com o portal real ou com uma implementação falsa (usada nos testes, sem abrir o navegador).

Onde não há estado a guardar (conversões de texto, slug), foram usadas **funções simples** em vez de classes.

### Padrões de código

- PEP 8 verificada com **Ruff** (lint + formatação), configurado no `pyproject.toml`.
- Type hints em todas as funções públicas e docstrings curtas.
- Nomes de domínio em português (`municipio`, `populacao_estimada`), seguindo as colunas pedidas.
- `logging` para o progresso e avisos; `print` apenas no menu.
- Commits no padrão Conventional Commits (`feat:`, `fix:`, `refactor:`...).

---

## Decisões técnicas

- **Um navegador para todos os municípios:** o Playwright é aberto uma vez e reutilizado; ele é encerrado via gerenciador de contexto (`with`) mesmo se houver erro ou Ctrl+C.
- **O navegador só abre na coleta:** a aplicação recebe o portal como "fábrica", então ele não fica aberto enquanto o usuário escolhe a UF no menu.
- **Espera pelo conteúdo, não por tempo fixo:** após `page.goto(..., wait_until="domcontentloaded")`, o código aguarda o seletor `div.indicador .ind-value` antes de chamar `page.content()`.
- **Extração pelo rótulo exato:** a página tem "População **no último censo**" e "População **estimada**"; buscar só por "População" pegaria o valor errado.
- **Falha de um município não interrompe a coleta:** qualquer erro do portal (página inexistente, timeout, bloqueio) é registrado com o motivo e a coleta segue com os demais.
- **Tipos do pandas que aceitam vazio (`Int64`, `Float64`):** com `int` comum, um campo ausente viraria `NaN` decimal.
- **Uso responsável do portal:** pausa de 1 s entre páginas.
- **Resumo separado da gravação:** `GeradorResumo` monta as tabelas (DataFrames) e não sabe nada de Excel; o `ExportadorExcel` recebe esse gerador pelo construtor e só grava.
- **Testabilidade como critério de design:** o `IBGEAPIClient` aceita um `transport` do httpx opcional e o pipeline aceita qualquer `FonteHTML`, o que permite testar tudo sem rede e sem navegador.

## Problemas encontrados e como foram resolvidos

1. **Timeout ao carregar o portal.** O `page.goto` com o padrão `wait_until="load"` passava de 30 s, porque a página carrega muitos recursos externos. Solução: `domcontentloaded` + espera pelo seletor do conteúdo relevante.

2. **Verificação anti-bot (Cloudflare).** Em modo headless, o HTML salvo era a tela "Just a moment...", e não a página do município. Solução: navegador visível (`PORTAL_HEADLESS = False` no `config.py`), espera pelo seletor real e detecção explícita do bloqueio como erro, em vez de salvar conteúdo inválido.

3. **Redirecionamento silencioso para a página do Brasil.** URLs inexistentes não retornam 404: o portal redireciona para a página do país, que tem a mesma estrutura de indicadores. O parser chegou a gravar a área do Brasil (8.509.360,85 km²) como se fosse do município. Solução: comparar a URL final com a solicitada e tratar a diferença como "URL não encontrada".

4. **Nomes com apóstrofo.** "Olho d'Água das Flores" gerava `olho-d-agua-das-flores`, que não existe. Verificando no portal, o formato correto é `olho-dagua-das-flores`: o apóstrofo é removido, sem virar hífen. Acentos são removidos com `unicodedata` e espaços viram hífen.

5. **Ordenação com acentos.** O `sorted()` padrão compara por código Unicode e jogava "Água Preta" para o fim da lista, o que mudaria quais seriam os "5 primeiros". Solução: chave de ordenação que ignora acentos e maiúsculas.

6. **Um timeout derrubava a coleta inteira.** Na coleta dos 185 municípios de PE, um timeout em Cupira interrompia o programa e descartava os 54 municípios já coletados. Solução: capturar qualquer erro do portal por município, registrar e continuar.

7. **Hierarquia nula na API.** Alguns municípios podem vir com `microrregiao` nula; o cliente usa o caminho alternativo por `regiao-imediata` antes de cair no dado do estado escolhido.

8. **`requirements.txt` em UTF-16.** O `pip freeze >` no PowerShell gera UTF-16, o que pode quebrar a instalação em Linux/macOS. O arquivo foi reescrito em UTF-8 com apenas as dependências diretas; as de desenvolvimento ficaram em `requirements-dev.txt`.

9. **Resumo inconsistente com a planilha (encontrado pelos testes).** Com um município duplicado, a aba de dados removia a duplicata, mas o resumo contava o registro duas vezes. O resumo passou a contar por código IBGE, coerente com a regra de não duplicar municípios.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -v
```

São **56 testes** que rodam em cerca de 1 segundo, **sem internet e sem navegador**:

| Arquivo | O que cobre |
|---|---|
| `test_cidade_parser.py` | Extração a partir do **HTML real de Recife** (`tests/fixtures/recife.html`), escolha da população estimada (e não a do censo), HTML sem indicadores e campo ausente |
| `test_ibge_api.py` | API simulada com `httpx.MockTransport`: ordenação, `microrregiao` nula, endpoint consultado, HTTP 500, JSON inválido, formato inesperado, lista vazia e timeout |
| `test_pipeline.py` | Portal falso: coleta completa, falha em um município sem interromper os demais e registro da URL consultada |
| `test_exporter.py` | Colunas na ordem do enunciado, remoção de duplicados, ordenação sem acento, tipos, campos vazios e aba de resumo |
| `test_cli.py` | Validação da UF (número ou sigla) e do limite (padrão, máximo e entradas inválidas) |
| `test_texto.py` | Slug da URL, números no formato brasileiro, ano de referência e ordenação |

Para atualizar o HTML de exemplo: `python scripts/salvar_fixture.py pe recife`.

O código também é verificado com `ruff check .` e `ruff format --check .`.

## Diferenciais implementados

- ✅ **Testes automatizados** da extração a partir de um HTML de exemplo (e das demais camadas).
- ✅ **Continuar com os demais municípios quando uma página falhar**, registrando o motivo.
- ✅ **Aba adicional no Excel** com resumo da coleta, UF selecionada, erros e dados ausentes.
- ⬜ Indicador adicional da API de Agregados (não implementado).

## Limitações conhecidas

- **Navegador visível:** por causa da verificação anti-bot do portal, a coleta roda com o navegador aberto na tela; em servidores sem interface gráfica seria necessário um display virtual (ex.: Xvfb). O modo headless pode ser ativado em `config.py`, mas tende a ser bloqueado.
- **Dependência do HTML do portal:** a extração depende das classes `div.indicador`, `.ind-label` e `.ind-value`. Se o IBGE mudar o layout, os campos passam a vir vazios (e são registrados no log como ausentes), mas o programa não quebra nem inventa valores.
- **Slug da URL:** a URL é montada a partir do nome do município. Municípios com grafia muito diferente no portal podem não ser encontrados; nesse caso eles aparecem no resumo como "URL não encontrada".
- **Tempo de execução:** cada município leva alguns segundos (carregamento + pausa). Coletar um estado inteiro pode levar vários minutos.
- **Dados ausentes:** quando um campo não existe na página de um município, a célula fica vazia, o aviso `"<município>: campos ausentes na página: [...]"` é exibido no log e o município é listado na aba `resumo`. Nos testes realizados (PE, TO, BA, AL), todos os campos estavam disponíveis.
- **Dados dinâmicos:** os valores (prefeito, população estimada e anos de referência) são os exibidos no portal na data da coleta e podem mudar com atualizações do IBGE.

## Fontes

- API de Localidades do IBGE — https://servicodados.ibge.gov.br/api/docs/localidades
  - Estados: `https://servicodados.ibge.gov.br/api/v1/localidades/estados`
  - Municípios por UF: `https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios`
- Portal Cidades e Estados — https://www.ibge.gov.br/cidades-e-estados
