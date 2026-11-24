# Desafio Técnico QCA — Coleta de dados de municípios do IBGE

Aplicação em Python que lista os estados brasileiros pela **API de Localidades do IBGE**, deixa o usuário escolher uma UF, visita a página de cada município no portal **Cidades e Estados** e gera uma planilha Excel com os dados coletados. Como indicador adicional, a planilha traz o **PIB de cada município**, obtido na **API de Agregados**.

```
listar estados (API) → escolher UF → consultar municípios (API) → coletar no portal (Playwright) → extrair (BeautifulSoup) → exportar Excel (pandas)
```

| Biblioteca | Uso no projeto |
|---|---|
| **httpx** | Consulta às APIs REST de Localidades (estados e municípios) e de Agregados (PIB) |
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
| `pib_mil_reais` | Decimal (Mil Reais) | API de Agregados *(diferencial)* |
| `ano_pib` | Inteiro | API de Agregados *(diferencial)* |

As 12 primeiras colunas são as exigidas pelo enunciado, na ordem pedida; as duas do PIB vêm depois, para não alterar essa estrutura.

Números no formato brasileiro (`1.588.983`, `218,843`) são convertidos para tipos numéricos, e os anos de referência ficam em colunas separadas dos valores. **Dados ausentes ficam vazios** — nenhum valor é inventado ou preenchido com zero.

### Aba `resumo`

A planilha tem uma segunda aba que registra a execução, para que essas informações não fiquem só no terminal:

- **Resumo da coleta:** UF selecionada, data, municípios processados, coletados com sucesso, quantidade com falha e quantidade com campos ausentes.
- **Municípios com falha:** código IBGE, nome, URL tentada e motivo (URL não encontrada, timeout, bloqueio...).
- **Campos ausentes:** municípios coletados em que algum campo não foi encontrado na página, e quais campos.
- **Avisos:** falhas que não impedem a planilha, como a API de Agregados estar indisponível.

O resumo também informa quantos municípios tiveram o PIB obtido.

### Indicador adicional: PIB dos municípios

O PIB vem da **tabela 5938** do SIDRA ("PIB dos Municípios"), **variável 37** (Produto Interno Bruto a preços correntes, em Mil Reais), no **último ano disponível** (`periodos/-1`, hoje 2023).

Antes de implementar, os metadados da tabela foram consultados: ela **não tem a variável "PIB per capita"**. Calcular o per capita aqui misturaria o PIB de 2023 com a população estimada de outro ano, gerando um número impreciso. Por isso o indicador é o PIB em si.

---

## Arquitetura

O projeto segue uma **arquitetura em camadas**, e cada camada é uma pasta dentro de `src/ibge_coleta/`. As camadas conversam por contratos (`Protocol`) e modelos de dados comuns, e as dependências apontam sempre para dentro, em direção ao domínio:

```
apresentacao  ──▶  aplicacao  ──▶  dominio  ◀──  infraestrutura
```

| Camada | Pasta | Responsabilidade | Depende de |
|---|---|---|---|
| **Apresentação** | `apresentacao/` | Menu de terminal (`input`/`print`) | aplicação, domínio |
| **Aplicação** | `aplicacao/` | Casos de uso e orquestração da coleta | só do domínio (contratos) |
| **Domínio** | `dominio/` | Modelos, contratos (`Protocol`) e exceções | nada |
| **Infraestrutura** | `infraestrutura/` | APIs (httpx), portal (Playwright), parser (BeautifulSoup) e Excel (pandas) | domínio |

O `main.py` é a **raiz de composição**: o único ponto que conhece as implementações concretas e as entrega às outras camadas. Nem a aplicação nem o domínio importam httpx, Playwright, BeautifulSoup ou pandas.

```
desafio-qca-ibge/
├── main.py                         ponto de entrada e raiz de composição
├── src/ibge_coleta/
│   ├── apresentacao/
│   │   └── cli.py                  menu de terminal
│   ├── aplicacao/
│   │   ├── app.py                  casos de uso (AplicacaoColeta)
│   │   └── pipeline.py             coleta município a município (PipelineColeta)
│   ├── dominio/
│   │   ├── models.py               Estado, Municipio, DadosPortal, IndicadorPIB, ResultadoColeta...
│   │   ├── interfaces.py           contratos: FonteLocalidades, FonteHTML, ParserCidade...
│   │   └── exceptions.py           ColetaError e suas especializações
│   ├── infraestrutura/
│   │   ├── clients/                http_base.py, ibge_api.py, agregados_api.py, portal.py
│   │   ├── parsers/                cidade_parser.py
│   │   └── exportacao/             exporter.py (Excel), resumo.py (aba de resumo)
│   ├── utils/texto.py              slug de URL, números no formato brasileiro, ordenação
│   └── config.py                   URLs, timeouts, limite padrão
├── scripts/salvar_fixture.py       salva o HTML de uma página para testes
├── tests/                          testes automatizados (pytest)
│   └── fixtures/recife.html        HTML real do portal, usado para testar o parser
├── output/                         planilha gerada
└── requirements.txt, requirements-dev.txt, pyproject.toml
```

### Princípios aplicados

**SOLID**, de forma pragmática (sem criar abstrações onde só existe uma implementação):

- **S — Responsabilidade única:** cada classe tem um papel: `IBGEAPIClient` só fala com a API de Localidades, `AgregadosAPIClient` só com a de Agregados, `PortalPlaywright` só navega, `CidadeParser` só interpreta HTML, `ExportadorExcel` só grava a planilha, `GeradorResumo` só monta as tabelas do resumo, `PipelineColeta` só orquestra.
- **O — Aberto/fechado:** o parser lê todos os indicadores da página de forma genérica e busca cada campo pelo rótulo; extrair um campo novo não exige mudar a lógica de leitura do HTML.
- **L / I — Substituição e interfaces enxutas:** os contratos em `dominio/interfaces.py` têm só os métodos necessários (`FonteHTML` tem 2, `ParserCidade` e `FonteIndicadorPIB` têm 1), e qualquer implementação que os cumpra pode ser usada no lugar da real.
- **D — Inversão de dependência:** `PipelineColeta` e `AplicacaoColeta` recebem suas dependências pelo construtor e dependem de abstrações, não de Playwright ou httpx. O único lugar que conhece as classes concretas é `criar_aplicacao()`, no `main.py` (raiz de composição); a camada de aplicação (`app.py`) importa apenas contratos.

**POO:**

- **Encapsulamento:** detalhes internos ficam em atributos e métodos privados (`_client`, `_page`, `_aguardar_conteudo`); quem usa as classes só vê métodos como `listar_municipios()` e `obter_html()`.
- **Abstração:** o pipeline pede "o HTML deste município" sem saber que existe um navegador.
- **Herança:** `IBGEAPIClient` e `AgregadosAPIClient` herdam de `ClienteHTTPIBGE`, que concentra a conexão httpx e o tratamento de timeout, erro HTTP, falha de conexão e JSON inválido (sem duplicar código). Também há a hierarquia de exceções `ColetaError` → `PortalError` → `PaginaNaoEncontradaError`, que permite tratar erros no nível certo de detalhe.
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
- **PIB em uma única requisição:** a API de Agregados aceita vários municípios de uma vez (`localidades=N6[cod1,cod2,...]`), então é feita uma chamada para todos, e não uma por município.
- **A coleta nunca é perdida na gravação:** se a planilha estiver aberta em outro programa, o exportador salva uma cópia com data e hora no nome em vez de falhar.
- **O PIB é um enriquecimento opcional:** se a API de Agregados falhar, a coleta principal continua, as colunas do PIB ficam vazias e a falha é registrada na seção "Avisos" do resumo.
- **Testabilidade como critério de design:** o `IBGEAPIClient` aceita um `transport` do httpx opcional e o pipeline aceita qualquer `FonteHTML`, o que permite testar tudo sem rede e sem navegador.

## Problemas encontrados e como foram resolvidos

1. **Timeout ao carregar o portal.** O `page.goto` com o padrão `wait_until="load"` passava de 30 s, porque a página carrega muitos recursos externos. Solução: `domcontentloaded` + espera pelo seletor do conteúdo relevante.

2. **Verificação anti-bot (Cloudflare).** Em modo headless, o HTML salvo era a tela "Just a moment...", e não a página do município. Solução: navegador visível (`PORTAL_HEADLESS = False` no `config.py`), espera pelo seletor real e detecção explícita do bloqueio como erro, em vez de salvar conteúdo inválido. Depois que a espera inteligente foi implementada, o headless foi testado de novo: o portal respondeu **HTTP 403** com a tela de verificação para os 5 municípios de PA, enquanto com o navegador visível a coleta completa de PE teve 185 de 185. A decisão foi mantida, e o tratamento foi refinado: um 403 com a tela de verificação não é descartado na hora; o código espera o conteúdo (a verificação pode se resolver sozinha) e, se não liberar, registra "Verificação anti-bot não concluída" em vez de um erro HTTP genérico.

3. **Redirecionamento silencioso para a página do Brasil.** URLs inexistentes não retornam 404: o portal redireciona para a página do país, que tem a mesma estrutura de indicadores. O parser chegou a gravar a área do Brasil (8.509.360,85 km²) como se fosse do município. Solução: comparar a URL final com a solicitada e tratar a diferença como "URL não encontrada".

4. **Nomes com apóstrofo.** "Olho d'Água das Flores" gerava `olho-d-agua-das-flores`, que não existe. Verificando no portal, o formato correto é `olho-dagua-das-flores`: o apóstrofo é removido, sem virar hífen. Acentos são removidos com `unicodedata` e espaços viram hífen.

5. **Ordenação com acentos.** O `sorted()` padrão compara por código Unicode e jogava "Água Preta" para o fim da lista, o que mudaria quais seriam os "5 primeiros". Solução: chave de ordenação que ignora acentos e maiúsculas.

6. **Um timeout derrubava a coleta inteira.** Na coleta dos 185 municípios de PE, um timeout em Cupira interrompia o programa e descartava os 54 municípios já coletados. Solução: capturar qualquer erro do portal por município, registrar e continuar.

7. **Hierarquia nula na API.** Alguns municípios podem vir com `microrregiao` nula; o cliente usa o caminho alternativo por `regiao-imediata` antes de cair no dado do estado escolhido.

8. **`requirements.txt` em UTF-16.** O `pip freeze >` no PowerShell gera UTF-16, o que pode quebrar a instalação em Linux/macOS. O arquivo foi reescrito em UTF-8 com apenas as dependências diretas; as de desenvolvimento ficaram em `requirements-dev.txt`.

9. **Resumo inconsistente com a planilha (encontrado pelos testes).** Com um município duplicado, a aba de dados removia a duplicata, mas o resumo contava o registro duas vezes. O resumo passou a contar por código IBGE, coerente com a regra de não duplicar municípios.

10. **Variável de PIB per capita inexistente.** A primeira tentativa usou um código de variável que não existe na tabela 5938, e a API respondeu erro 500. A exploração dos metadados mostrou as variáveis disponíveis, e o indicador passou a ser o PIB a preços correntes (variável 37).

11. **Um código inválido derruba a consulta do lote inteiro.** Testando a API de Agregados com um código válido e um inexistente, a resposta foi erro 500 para todos. O cliente passou a consultar município a município quando o lote falha, preservando os dados dos válidos.

12. **Falhas encontradas na revisão final (testes de estresse).** Simulando cenários fora do caminho feliz, três falhas apareceram e foram corrigidas, cada uma com teste:
    - **Planilha aberta no Excel:** no Windows o arquivo fica bloqueado e a gravação falhava com traceback, perdendo minutos de coleta. Agora a planilha é salva como uma cópia com data e hora no nome (`municipios_pe_AAAAMMDD_HHMMSS.xlsx`), e o fato é registrado em "Avisos". Se nem a cópia puder ser gravada, o programa mostra uma mensagem pedindo para fechar o arquivo.
    - **JSON da API com estrutura inesperada:** um campo ausente gerava `KeyError` sem tratamento; na API de Agregados isso derrubava o programa depois da coleta inteira. Os dois clientes agora convertem esses casos em `IBGEAPIError("Formato inesperado...")`, e o PIB segue sendo opcional.
    - **Avisos só no Excel:** o resumo do terminal passou a exibi-los também.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -v
```

São **89 testes** que rodam em cerca de 1 segundo, **sem internet e sem navegador**:

| Arquivo | O que cobre |
|---|---|
| `test_cidade_parser.py` | Extração a partir do **HTML real de Recife** (`tests/fixtures/recife.html`), escolha da população estimada (e não a do censo), HTML sem indicadores e campo ausente |
| `test_ibge_api.py` | API simulada com `httpx.MockTransport`: ordenação, `microrregiao` nula, endpoint consultado, HTTP 500, JSON inválido, formato inesperado, JSON sem os campos esperados, lista vazia e timeout |
| `test_agregados_api.py` | API de Agregados simulada: uma requisição para vários municípios, valores indisponíveis (`-`, `...`, `X`), consulta um a um quando o lote falha, JSON malformado e lista vazia sem chamar a API |
| `test_portal.py` | `PortalPlaywright` com uma página falsa (sem abrir navegador): montagem da URL com acento, apóstrofo e hífen, HTML retornado, 404, outros erros HTTP, redirecionamento para a página do Brasil, bloqueio anti-bot (inclusive 403 com tela de verificação que se resolve ou não), página sem indicadores, timeout e uso sem abrir o navegador |
| `test_pipeline.py` | Portal falso: coleta completa, falha em um município sem interromper os demais, registro da URL, inclusão do PIB e falha da API de Agregados sem perder a coleta |
| `test_exporter.py` | Colunas na ordem do enunciado, colunas do PIB, remoção de duplicados, ordenação sem acento, tipos, campos vazios, aba de resumo, arquivo bloqueado (cópia com data e hora) e pasta de saída inválida |
| `test_cli.py` | Validação da UF (número ou sigla), do limite (padrão, máximo e entradas inválidas) e exibição dos avisos no resumo |
| `test_texto.py` | Slug da URL, números no formato brasileiro, ano de referência e ordenação |

Para atualizar o HTML de exemplo: `python scripts/salvar_fixture.py pe recife`.

O código também é verificado com `ruff check .` e `ruff format --check .`.

## Diferenciais implementados

- ✅ **Testes automatizados** da extração a partir de um HTML de exemplo (e das demais camadas).
- ✅ **Continuar com os demais municípios quando uma página falhar**, registrando o motivo.
- ✅ **Aba adicional no Excel** com resumo da coleta, UF selecionada, erros e dados ausentes.
- ✅ **Indicador adicional da API de Agregados:** PIB a preços correntes de cada município.

## Limitações conhecidas

- **Navegador visível:** por causa da verificação anti-bot do portal, a coleta roda com o navegador aberto na tela; em servidores sem interface gráfica seria necessário um display virtual (ex.: Xvfb). O modo headless pode ser ativado em `config.py`, mas nos testes foi bloqueado (HTTP 403 em todas as páginas).
- **Dependência do HTML do portal:** a extração depende das classes `div.indicador`, `.ind-label` e `.ind-value`. Se o IBGE mudar o layout, os campos passam a vir vazios (e são registrados no log como ausentes), mas o programa não quebra nem inventa valores.
- **Slug da URL:** a URL é montada a partir do nome do município. Municípios com grafia muito diferente no portal podem não ser encontrados; nesse caso eles aparecem no resumo como "URL não encontrada".
- **Tempo de execução:** cada município leva alguns segundos (carregamento + pausa). Coletar um estado inteiro pode levar vários minutos.
- **Dados ausentes:** quando um campo não existe na página de um município, a célula fica vazia, o aviso `"<município>: campos ausentes na página: [...]"` é exibido no log e o município é listado na aba `resumo`. Nos testes realizados (PE, TO, BA, AL), todos os campos estavam disponíveis — inclusive numa coleta completa de Pernambuco (185 de 185 municípios, sem falhas, sem campos ausentes e com PIB para todos). A planilha entregue em `output/municipios_pe.xlsx` usa o padrão pedido no enunciado (5 municípios).
- **PIB:** é o valor nominal (a preços correntes) do último ano publicado pelo IBGE, que tem alguns anos de defasagem em relação à data da coleta.
- **Dados dinâmicos:** os valores (prefeito, população estimada e anos de referência) são os exibidos no portal na data da coleta e podem mudar com atualizações do IBGE.

## Fontes

- API de Localidades do IBGE — https://servicodados.ibge.gov.br/api/docs/localidades
  - Estados: `https://servicodados.ibge.gov.br/api/v1/localidades/estados`
  - Municípios por UF: `https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios`
- Portal Cidades e Estados — https://www.ibge.gov.br/cidades-e-estados
- API de Agregados do IBGE — https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
  - PIB: `https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/-1/variaveis/37?localidades=N6[{códigos}]`
