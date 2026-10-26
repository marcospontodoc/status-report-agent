"""Nomes das abas, colunas e valores válidos do workbook de QA."""

SCENARIO_SHEET = "Cenarios de Teste"
BUG_SHEET = "Bugs"

SCENARIO_COLUMNS = (
    "US (User Story)",
    "ID",
    "Cenário",
    "Pré-condições",
    "Passo a passo",
    "Resultado esperado",
    "Resultado obtido",
    "Resultado",
    "Responsável",
)
BUG_COLUMNS = (
    "ID do Bug",
    "US (User Story)",
    "ID do Cenário",
    "Título",
    "Descrição",
    "Severidade",
    "Status",
    "Data de Abertura",
    "Responsável",
)

SCENARIO_RESULTS = ("Passou", "Falhou", "Bloqueado", "Não Executado")
BUG_SEVERITIES = ("Crítica", "Alta", "Média", "Baixa")
BUG_STATUSES = ("Aberto", "Em Análise", "Em Correção", "Pronto para Reteste", "Reaberto", "Fechado")
