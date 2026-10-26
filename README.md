# Agente de Status Reports Executivos de QA

## Objetivo

Desenvolver gradualmente um agente genérico que reúna informações de qualidade de software e produza status reports executivos em PowerPoint editável. A pessoa usuária conduzirá a evolução por instruções em linguagem natural no Codex; os arquivos necessários serão criados ou alterados durante essas etapas.

O agente deverá apoiar diferentes projetos sem depender de nomes, módulos, URLs, credenciais ou dados fixos. Não deverá inventar fatos quando as fontes forem incompletas. Relatórios futuros deverão separar dados confirmados, informações ausentes e riscos potenciais, explicando a evidência disponível.

## Arquitetura proposta

O fluxo é dividido em módulos para permitir trocar fontes e evoluir o relatório sem acoplar as partes:

1. **Conectores de fontes (`src/connectors/`)** — futuramente obtêm dados do Jira, do Excel e da documentação do projeto. Cada conector informa a origem e o contexto dos dados.
2. **Normalização e validação (`src/normalization/`)** — converte estruturas específicas das fontes para um modelo comum, valida campos e mantém referências à origem. O status de uma tarefa Jira permanece distinto do resultado de um teste.
3. **Análise executiva (`src/analysis/`)** — futuramente resume progresso, pendências, impedimentos, cobertura e riscos com base apenas nas evidências disponíveis. Distingue confirmações, lacunas e inferências de risco.
4. **Apresentação (`src/reporting/`)** — futuramente transforma a análise em slides PowerPoint editáveis, com informações rastreáveis às fontes.

### Fontes planejadas

- **Jira:** cards, status, responsáveis, prazos, atividades pendentes e impedimentos. O status de um card representa o fluxo de trabalho e não substitui o resultado de um caso de teste.
- **Excel:** fonte de gestão dos cenários de teste manuais, incluindo planejamento, status de execução, datas, resultados e bugs relacionados. O modelo futuro deve preservar múltiplas execuções e seu histórico.
- **Documentação do projeto:** requisitos, escopo, regras de negócio e critérios de aceite, usados para interpretar a cobertura e o contexto de QA.
- **Automação, etapa futura opcional:** relatórios de execução em JSON ou JUnit podem ser incorporados como fonte separada, sem apagar nem confundir o histórico manual do Excel.

Os leitores locais do Excel e da documentação do projeto estão implementados de forma independente. A integração com Jira e a geração de apresentações continuam como etapas futuras.

### Leitura local da documentação do projeto

`src/connectors/document_reader.py` extrai texto de arquivos Markdown (`.md` e `.markdown`), PDF (`.pdf`) e DOCX (`.docx`), sem alterar as fontes. Cada resultado inclui o caminho absoluto de origem e o formato. Arquivos inexistentes, vazios, sem texto extraível, formatos não suportados e problemas de leitura são apresentados como erros claros. PDFs compostos apenas por imagens não têm OCR nesta etapa e serão informados como sem texto extraível.

O leitor preserva a extração textual e identificação do arquivo; não interpreta requisitos, não valida seu conteúdo e não preenche informações ausentes. Em DOCX, texto de parágrafos, tabelas, cabeçalhos e rodapés é extraído; a ordem relativa entre parágrafos e tabelas pode não refletir exatamente a paginação visual.

Instale as dependências locais do projeto (além de `openpyxl`, `pypdf` lê PDF e `python-docx` lê DOCX):

```powershell
chcp 65001 | Out-Null
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Leia um documento e imprima sua origem, formato e texto extraído:

```powershell
python -X utf8 -m src.documentation_main --input inputs/documentacao/sistema-ficticio-derivado-da-fixture.md
```

Para PDF ou DOCX, informe o caminho do arquivo correspondente no argumento `--input`. A saída preserva a fonte para que o texto possa ser rastreado até o documento. O comando retorna `0` quando a leitura é concluída e `2` quando o arquivo não pode ser lido.

O documento em `inputs/documentacao/` é um material fictício baseado nos cenários e bugs sintéticos de `inputs/excel/modelo_qa_teste.xlsx`. Ele separa evidências derivadas da fixture de hipóteses complementares e não descreve um produto real.

### Análise consolidada local

`src/analysis/qa_analysis.py` consome o resultado já validado do Excel e o texto extraído pelo leitor documental. `src/consolidated_main.py` orquestra os leitores existentes, chama a validação e o resumo existentes e imprime a consolidação no terminal. Não altera as fontes.

A análise só extrai requisitos de seções cujo título identifica requisitos e de tabelas com colunas de referência/ID e descrição/comportamento; relações são confirmadas apenas por IDs explícitos: referência documental igual à User Story preenchida no Excel ou ID de cenário citado como evidência. Cenários sem vínculo encontrado e requisitos sem cenário são apresentados como lacunas de relação, não como prova de defeito ou ausência de requisito. Possíveis divergências se limitam a conflitos explícitos entre referências; o conteúdo semântico dos textos não é comparado automaticamente. O relatório mantém caminho do documento, linha no texto extraído e aba/linha do Excel sempre que disponíveis. Para PDF e DOCX, essa linha é a posição no texto extraído, não uma página física do documento. Se um PDF não preservar a estrutura de tabela na extração ou se a documentação estiver em prosa sem estrutura identificável, a análise registra a lacuna em vez de inferir relações.

Fatos registrados nas fontes são apresentados separadamente de hipóteses em seções explicitamente rotuladas como hipótese. Resultados `Falhou`, `Bloqueado`, `Não Executado` e bugs ainda não fechados podem gerar riscos potenciais, identificados como inferências e acompanhados da evidência. As métricas de execução e bugs vêm exclusivamente de `src/analysis/qa_summary.py`, preservando seus denominadores, filtros de IDs duplicados e regras de valores válidos.

Execute a análise com a planilha e um ou mais documentos locais:

```powershell
python -X utf8 -m src.consolidated_main `
  --excel inputs/excel/modelo_qa_teste.xlsx `
  --document inputs/documentacao/sistema-ficticio-derivado-da-fixture.md
```

Para fornecer mais de um documento, informe seus caminhos após `--document`:

```powershell
python -X utf8 -m src.consolidated_main `
  --excel inputs/excel/modelo_qa_teste.xlsx `
  --document inputs/documentacao/requisitos.md inputs/documentacao/criterios.pdf
```

### Leitura, validação e resumo do Excel

- `src/connectors/excel_reader.py` abre o arquivo em modo somente leitura, localiza as duas abas e mapeia colunas pelo cabeçalho. Ignora linhas totalmente vazias e mantém o número original da linha para diagnóstico.
- `src/qa_schema.py` mantém o contrato de abas, cabeçalhos e valores aceitos em um único lugar.
- `src/normalization/qa_data.py` normaliza valores e valida campos, IDs duplicados, resultados, severidades, status, datas e relações entre bugs e cenários.
- `src/analysis/qa_summary.py` calcula contagens e percentuais depois da validação. `src/main.py` apresenta o relatório no terminal.

O leitor exige os cabeçalhos do modelo, mas não depende da ordem das colunas. Os campos obrigatórios para cenário são `ID`, `Cenário` e `Resultado`. Para bug, são `ID do Bug`, `ID do Cenário`, `Título`, `Severidade` e `Status`. Campos opcionais vazios geram avisos; nenhum valor ausente é preenchido automaticamente. Valores inválidos e referências quebradas são listados como inconsistências com aba e linha.

Um registro de cenário com descrição ausente é marcado como inconsistente, mas ainda pode entrar no denominador se seu ID for único e seu resultado for válido: a contagem representa o resultado identificado e a inconsistência de descrição permanece visível à parte. IDs duplicados tornam todas as linhas daquele ID ambíguas e, por isso, elas não entram em contagens por ID. Para bugs, um ID único é contado como bug distinto mesmo quando outro campo contém erro; a linha e a categoria inválida continuam apontadas no relatório.

As linhas preenchidas são contadas como registros cadastrados. Cenários entram na distribuição de resultados somente quando têm ID único e resultado válido; `Não Executado` permanece como categoria própria. O denominador dos percentuais é a soma desses resultados contáveis. Linhas com ID duplicado são todas excluídas das contagens por ID. Bugs distintos são contados por ID único; duplicatas são sinalizadas e excluídas. As distribuições de severidade e status incluem apenas valores válidos.

#### Executar novamente

Instale Python 3 e as dependências locais do projeto:

```powershell
chcp 65001 | Out-Null
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Leia um arquivo informando seu caminho; a execução não modifica a planilha:

```powershell
python -X utf8 -m src.main --input inputs/excel/modelo_qa_teste.xlsx
```

Para executar a suíte automatizada:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Se a pessoa usuária quiser repetir a leitura pelo Codex, basta pedir para executar `python -X utf8 -m src.main --input <caminho-do-arquivo.xlsx>` e apresentar a saída. No Windows PowerShell, `chcp 65001 | Out-Null` ajuda a exibir corretamente os rótulos em português. O Codex deve usar um runtime Python local disponível, sem editar o arquivo de origem. A CLI retorna código `0` quando não há inconsistências de registro, `1` quando há registros inconsistentes e `2` quando não consegue ler o arquivo ou o esquema.

`inputs/excel/modelo_qa_teste.xlsx` é uma fixture inteiramente fictícia para validação inicial, identificada em `inputs/excel/LEIA-ME_modelo_qa_teste.md`. Ela não representa resultados de nenhum projeto real.

## Estrutura inicial

```text
AGENTS.md                    Instruções permanentes do projeto
README.md                    Objetivo, arquitetura e roteiro
instructions/                Instruções reutilizáveis futuras
docs/                        Decisões de arquitetura e documentação técnica futura
inputs/
  jira/                      Área prevista para exportações/entradas do Jira
  excel/                     Área prevista para planilhas de QA manuais
  documentacao/              Documentação de projeto para leitura local
  project-docs/              Área prevista para requisitos e documentação
  automation-reports/        Área prevista para relatórios JSON/JUnit futuros
outputs/                     Área prevista para relatórios gerados
src/
  connectors/                Integração futura com as fontes
  normalization/              Modelo comum e validação futuros
  analysis/                   Análise executiva futura
  reporting/                  Geração futura do PowerPoint editável
```

As pastas de entrada e saída são apenas uma organização inicial; nesta etapa não há leitores, dados de exemplo nem arquivos de relatório. Segredos não devem ser colocados nessas pastas nem versionados.

## Roteiro de evolução

1. **Fundação:** princípios, arquitetura e estrutura inicial do projeto.
2. **Modelo e leitura local do Excel:** planilha manual, leitor, validação, resumo, testes e instruções de execução.
3. **Jira:** escolher e implementar um modo de leitura apropriado (por exemplo, exportação local ou API), com credenciais fora do repositório.
4. **Documentação do projeto:** leitor local rastreável de Markdown, PDF e DOCX implementado; interpretação/consolidação de requisitos, escopo, regras e critérios de aceite permanece futura.
5. **Análise executiva consolidada:** análise local inicial implementada para Excel e documentação; integração com Jira e análise semântica automatizada permanecem futuras.
6. **PowerPoint editável:** criar slides com texto, tabelas e gráficos editáveis, origem dos dados e data de referência confirmada; validar o conteúdo e a apresentação.
7. **Automação e evolução:** avaliar suporte opcional a JSON/JUnit, mantendo os resultados automatizados separados e conciliáveis com o histórico manual.

Cada etapa deverá ser solicitada e concluída separadamente. Dependências e ferramentas serão escolhidas quando necessárias, priorizando opções gratuitas e locais.
