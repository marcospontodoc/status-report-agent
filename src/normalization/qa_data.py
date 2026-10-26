"""Contrato, normalização e validação dos registros manuais de QA."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from src.connectors.excel_reader import ExcelQAInput, ExcelRow
from src.qa_schema import BUG_COLUMNS, BUG_SEVERITIES, BUG_STATUSES, BUG_SHEET, SCENARIO_COLUMNS, SCENARIO_RESULTS, SCENARIO_SHEET


@dataclass(frozen=True)
class Issue:
    """Inconsistência bloqueante ou aviso de dado ausente."""

    level: str
    sheet: str
    row_number: int
    field: str
    message: str


@dataclass(frozen=True)
class ScenarioRecord:
    row_number: int
    user_story: str | None
    identifier: str | None
    description: str | None
    preconditions: str | None
    steps: str | None
    expected_result: str | None
    observed_result: str | None
    result: str | None
    owner: str | None


@dataclass(frozen=True)
class BugRecord:
    row_number: int
    identifier: str | None
    user_story: str | None
    scenario_id: str | None
    title: str | None
    description: str | None
    severity: str | None
    status: str | None
    opened_date: date | datetime | None
    owner: str | None


@dataclass(frozen=True)
class ValidationReport:
    scenarios: tuple[ScenarioRecord, ...]
    bugs: tuple[BugRecord, ...]
    issues: tuple[Issue, ...]
    scenario_outcomes: tuple[ScenarioRecord, ...]
    distinct_bugs: tuple[BugRecord, ...]
    valid_scenario_rows: int
    invalid_scenario_rows: int
    valid_bug_rows: int
    invalid_bug_rows: int


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _id_key(value: str | None) -> str | None:
    return value.casefold() if value else None


def _enum_value(value: Any, allowed: tuple[str, ...]) -> str | None:
    text = _text(value)
    if text is None:
        return None
    lookup = {item.casefold(): item for item in allowed}
    return lookup.get(text.casefold())


def _row_issue(level: str, row: ExcelRow, field: str, message: str) -> Issue:
    return Issue(level=level, sheet=row.sheet, row_number=row.row_number, field=field, message=message)


def _record_errors(issues: list[Issue], sheet: str) -> set[int]:
    return {issue.row_number for issue in issues if issue.sheet == sheet and issue.level == "error"}


def validate_qa_data(data: ExcelQAInput) -> ValidationReport:
    """Normaliza valores, valida consistência e mantém origem/linha para auditoria.

    Linhas com IDs duplicados são todas excluídas de contagens por ID. Um cenário
    entra na distribuição de resultados quando tem ID único e resultado válido;
    outras falhas de descrição continuam sinalizadas separadamente.
    """

    issues: list[Issue] = []
    scenarios: list[ScenarioRecord] = []
    bugs: list[BugRecord] = []

    for row in data.scenarios:
        values = row.values
        identifier = _text(values.get("ID"))
        result_text = _text(values.get("Resultado"))
        result = _enum_value(result_text, SCENARIO_RESULTS)
        description = _text(values.get("Cenário"))

        if identifier is None:
            issues.append(_row_issue("error", row, "ID", "Campo obrigatório ausente; cenário sem ID não pode ser contado."))
        if description is None:
            issues.append(_row_issue("error", row, "Cenário", "Campo obrigatório ausente."))
        if result_text is None:
            issues.append(_row_issue("error", row, "Resultado", "Resultado ausente; não será presumido como aprovado."))
        elif result is None:
            issues.append(
                _row_issue(
                    "error",
                    row,
                    "Resultado",
                    f"Valor inválido '{result_text}'. Valores aceitos: {', '.join(SCENARIO_RESULTS)}.",
                )
            )

        normalized = ScenarioRecord(
            row_number=row.row_number,
            user_story=_text(values.get("US (User Story)")),
            identifier=identifier,
            description=description,
            preconditions=_text(values.get("Pré-condições")),
            steps=_text(values.get("Passo a passo")),
            expected_result=_text(values.get("Resultado esperado")),
            observed_result=_text(values.get("Resultado obtido")),
            result=result,
            owner=_text(values.get("Responsável")),
        )
        scenarios.append(normalized)

        optional_fields = (
            ("US (User Story)", normalized.user_story),
            ("Pré-condições", normalized.preconditions),
            ("Passo a passo", normalized.steps),
            ("Resultado esperado", normalized.expected_result),
            ("Resultado obtido", normalized.observed_result),
            ("Responsável", normalized.owner),
        )
        for field, field_value in optional_fields:
            if field_value is None:
                issues.append(_row_issue("warning", row, field, "Informação ausente; a leitura continua, mas a análise pode ficar limitada."))

    scenario_id_counts = Counter(_id_key(record.identifier) for record in scenarios if record.identifier)
    for row, record in zip(data.scenarios, scenarios):
        if record.identifier and scenario_id_counts[_id_key(record.identifier)] > 1:
            issues.append(_row_issue("error", row, "ID", f"ID duplicado '{record.identifier}'; todas as linhas com esse ID serão excluídas das contagens."))

    unique_scenarios_by_id = {
        _id_key(record.identifier): record
        for record in scenarios
        if record.identifier and scenario_id_counts[_id_key(record.identifier)] == 1
    }

    for row in data.bugs:
        values = row.values
        identifier = _text(values.get("ID do Bug"))
        scenario_id = _text(values.get("ID do Cenário"))
        title = _text(values.get("Título"))
        severity_text = _text(values.get("Severidade"))
        status_text = _text(values.get("Status"))
        severity = _enum_value(severity_text, BUG_SEVERITIES)
        status = _enum_value(status_text, BUG_STATUSES)
        opened_value = values.get("Data de Abertura")
        opened_date: date | datetime | None = opened_value if isinstance(opened_value, (date, datetime)) else None

        if identifier is None:
            issues.append(_row_issue("error", row, "ID do Bug", "Campo obrigatório ausente; bug sem ID não pode ser contado."))
        if scenario_id is None:
            issues.append(_row_issue("error", row, "ID do Cenário", "Campo obrigatório ausente."))
        if title is None:
            issues.append(_row_issue("error", row, "Título", "Campo obrigatório ausente."))
        if severity_text is None:
            issues.append(_row_issue("error", row, "Severidade", "Severidade ausente."))
        elif severity is None:
            issues.append(_row_issue("error", row, "Severidade", f"Valor inválido '{severity_text}'. Valores aceitos: {', '.join(BUG_SEVERITIES)}."))
        if status_text is None:
            issues.append(_row_issue("error", row, "Status", "Status ausente."))
        elif status is None:
            issues.append(_row_issue("error", row, "Status", f"Valor inválido '{status_text}'. Valores aceitos: {', '.join(BUG_STATUSES)}."))
        if opened_value is not None and opened_date is None:
            issues.append(_row_issue("error", row, "Data de Abertura", "A data preenchida não é uma data Excel reconhecida."))

        normalized = BugRecord(
            row_number=row.row_number,
            identifier=identifier,
            user_story=_text(values.get("US (User Story)")),
            scenario_id=scenario_id,
            title=title,
            description=_text(values.get("Descrição")),
            severity=severity,
            status=status,
            opened_date=opened_date,
            owner=_text(values.get("Responsável")),
        )
        bugs.append(normalized)

        if scenario_id is not None:
            referenced_scenario = unique_scenarios_by_id.get(_id_key(scenario_id))
            if referenced_scenario is None:
                issues.append(_row_issue("error", row, "ID do Cenário", f"Cenário '{scenario_id}' não existe com um ID único na aba '{SCENARIO_SHEET}'."))
            elif normalized.user_story and referenced_scenario.user_story:
                if _id_key(normalized.user_story) != _id_key(referenced_scenario.user_story):
                    issues.append(_row_issue("error", row, "US (User Story)", "A User Story do bug não corresponde à User Story do cenário relacionado."))

        for field, field_value in (
            ("US (User Story)", normalized.user_story),
            ("Descrição", normalized.description),
            ("Data de Abertura", normalized.opened_date),
            ("Responsável", normalized.owner),
        ):
            if field_value is None:
                issues.append(_row_issue("warning", row, field, "Informação ausente; a leitura continua, mas a análise pode ficar limitada."))

    bug_id_counts = Counter(_id_key(record.identifier) for record in bugs if record.identifier)
    for row, record in zip(data.bugs, bugs):
        if record.identifier and bug_id_counts[_id_key(record.identifier)] > 1:
            issues.append(_row_issue("error", row, "ID do Bug", f"ID duplicado '{record.identifier}'; todas as linhas com esse ID serão excluídas das contagens."))

    scenario_outcomes = tuple(
        record
        for record in scenarios
        if record.identifier
        and scenario_id_counts[_id_key(record.identifier)] == 1
        and record.result in SCENARIO_RESULTS
    )
    distinct_bugs = tuple(
        record
        for record in bugs
        if record.identifier and bug_id_counts[_id_key(record.identifier)] == 1
    )

    scenario_error_rows = _record_errors(issues, SCENARIO_SHEET)
    bug_error_rows = _record_errors(issues, BUG_SHEET)
    return ValidationReport(
        scenarios=tuple(scenarios),
        bugs=tuple(bugs),
        issues=tuple(sorted(issues, key=lambda item: (0 if item.sheet == SCENARIO_SHEET else 1, item.row_number, item.level, item.field))),
        scenario_outcomes=scenario_outcomes,
        distinct_bugs=distinct_bugs,
        valid_scenario_rows=len(scenarios) - len(scenario_error_rows),
        invalid_scenario_rows=len(scenario_error_rows),
        valid_bug_rows=len(bugs) - len(bug_error_rows),
        invalid_bug_rows=len(bug_error_rows),
    )
