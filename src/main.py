"""CLI local para ler, validar e resumir uma planilha de QA."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.analysis.qa_summary import QASummary, summarize_qa
from src.connectors.excel_reader import ExcelReadError, read_qa_workbook
from src.normalization.qa_data import Issue, validate_qa_data


def _format_issues(title: str, issues: tuple[Issue, ...], level: str) -> list[str]:
    lines = [title]
    selected = [issue for issue in issues if issue.level == level]
    if not selected:
        return lines + ["  Nenhum."]
    for issue in selected:
        lines.append(f"  - Aba '{issue.sheet}', linha {issue.row_number}, campo '{issue.field}': {issue.message}")
    return lines


def format_report(source: Path, summary: QASummary, issues: tuple[Issue, ...]) -> str:
    lines = [
        f"Fonte Excel: {source}",
        "",
        "CENÁRIOS",
        f"  Total cadastrado (linhas não vazias): {summary.total_scenarios_registered}",
        f"  Registros válidos: {summary.valid_scenario_rows}",
        f"  Registros com inconsistências: {summary.invalid_scenario_rows}",
        f"  Registros sem resultado válido: {summary.scenarios_without_valid_result}",
        f"  Registros fora do denominador de resultados: {summary.scenarios_excluded_from_result_denominator}",
        f"  Denominador dos percentuais (ID único e resultado válido): {summary.scenario_result_denominator}",
    ]
    for result, count in summary.scenario_result_counts.items():
        percentage = summary.scenario_result_percentages[result]
        percent_text = "n/a" if percentage is None else f"{percentage:.2f}%"
        lines.append(f"  {result}: {count} ({percent_text})")

    lines.extend(
        [
            "",
            "BUGS",
            f"  Total de bugs distintos (IDs únicos identificados): {summary.distinct_bug_count}",
            f"  Registros válidos: {summary.valid_bug_rows}",
            f"  Registros com inconsistências: {summary.invalid_bug_rows}",
            "  Por severidade:",
        ]
    )
    lines.extend(f"    {severity}: {count}" for severity, count in summary.bug_severity_counts.items())
    lines.append("  Por status:")
    lines.extend(f"    {status}: {count}" for status, count in summary.bug_status_counts.items())
    lines.append(f"  Bugs sem severidade válida: {summary.bugs_without_valid_severity}")
    lines.append(f"  Bugs sem status válido: {summary.bugs_without_valid_status}")
    lines.extend(["", *_format_issues("INCONSISTÊNCIAS", issues, "error"), "", *_format_issues("AVISOS SOBRE INFORMAÇÕES AUSENTES", issues, "warning")])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lê e valida uma planilha Excel de testes manuais de QA.")
    parser.add_argument("--input", required=True, type=Path, help="Caminho do arquivo .xlsx a analisar.")
    args = parser.parse_args(argv)

    try:
        source = read_qa_workbook(args.input)
    except ExcelReadError as exc:
        print(f"Erro de leitura: {exc}", file=sys.stderr)
        return 2

    validation = validate_qa_data(source)
    summary = summarize_qa(validation)
    print(format_report(source.source_path, summary, validation.issues))
    return 1 if validation.invalid_scenario_rows or validation.invalid_bug_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
