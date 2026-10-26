"""Indicadores derivados dos registros normalizados e validados."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.normalization.qa_data import BUG_SEVERITIES, BUG_STATUSES, SCENARIO_RESULTS, ValidationReport


@dataclass(frozen=True)
class QASummary:
    total_scenarios_registered: int
    valid_scenario_rows: int
    invalid_scenario_rows: int
    scenarios_without_valid_result: int
    scenarios_excluded_from_result_denominator: int
    scenario_result_denominator: int
    scenario_result_counts: dict[str, int]
    scenario_result_percentages: dict[str, float | None]
    distinct_bug_count: int
    valid_bug_rows: int
    invalid_bug_rows: int
    bug_severity_counts: dict[str, int]
    bug_status_counts: dict[str, int]
    bugs_without_valid_severity: int
    bugs_without_valid_status: int


def summarize_qa(validation: ValidationReport) -> QASummary:
    """Calcula contagens sem tratar estados ausentes como sucesso."""

    result_counter = Counter(record.result for record in validation.scenario_outcomes)
    result_counts = {result: result_counter.get(result, 0) for result in SCENARIO_RESULTS}
    result_denominator = sum(result_counts.values())
    percentages = {
        result: (round(result_counts[result] * 100 / result_denominator, 2) if result_denominator else None)
        for result in SCENARIO_RESULTS
    }

    severity_counter = Counter(bug.severity for bug in validation.distinct_bugs if bug.severity in BUG_SEVERITIES)
    status_counter = Counter(bug.status for bug in validation.distinct_bugs if bug.status in BUG_STATUSES)
    severity_counts = {severity: severity_counter.get(severity, 0) for severity in BUG_SEVERITIES}
    status_counts = {status: status_counter.get(status, 0) for status in BUG_STATUSES}

    return QASummary(
        total_scenarios_registered=len(validation.scenarios),
        valid_scenario_rows=validation.valid_scenario_rows,
        invalid_scenario_rows=validation.invalid_scenario_rows,
        scenarios_without_valid_result=sum(record.result is None for record in validation.scenarios),
        scenarios_excluded_from_result_denominator=len(validation.scenarios) - len(validation.scenario_outcomes),
        scenario_result_denominator=result_denominator,
        scenario_result_counts=result_counts,
        scenario_result_percentages=percentages,
        distinct_bug_count=len(validation.distinct_bugs),
        valid_bug_rows=validation.valid_bug_rows,
        invalid_bug_rows=validation.invalid_bug_rows,
        bug_severity_counts=severity_counts,
        bug_status_counts=status_counts,
        bugs_without_valid_severity=sum(bug.severity is None for bug in validation.distinct_bugs),
        bugs_without_valid_status=sum(bug.status is None for bug in validation.distinct_bugs),
    )
