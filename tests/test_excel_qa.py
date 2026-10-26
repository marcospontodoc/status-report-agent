from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import unittest

from openpyxl import Workbook

from src.analysis.qa_summary import summarize_qa
from src.connectors.excel_reader import read_qa_workbook
from src.main import format_report
from src.normalization.qa_data import validate_qa_data
from src.qa_schema import BUG_COLUMNS, BUG_SHEET, SCENARIO_COLUMNS, SCENARIO_SHEET


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEST_WORKBOOK = REPOSITORY_ROOT / "inputs" / "excel" / "modelo_qa_teste.xlsx"


def scenario(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "US (User Story)": "US-UNIT-01",
        "ID": "TC-UNIT-01",
        "Cenário": "Cenário sintético de teste unitário",
        "Pré-condições": "Pré-condição sintética",
        "Passo a passo": "Executar uma ação sintética",
        "Resultado esperado": "Comportamento esperado sintético",
        "Resultado obtido": "Comportamento observado sintético",
        "Resultado": "Passou",
        "Responsável": "Responsável sintético",
    }
    row.update(overrides)
    return row


def bug(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "ID do Bug": "BUG-UNIT-01",
        "US (User Story)": "US-UNIT-01",
        "ID do Cenário": "TC-UNIT-01",
        "Título": "Bug sintético de teste unitário",
        "Descrição": "Descrição sintética para teste automatizado.",
        "Severidade": "Média",
        "Status": "Aberto",
        "Data de Abertura": date(2026, 1, 15),
        "Responsável": "Responsável sintético",
    }
    row.update(overrides)
    return row


def write_workbook(
    path: Path,
    scenarios: list[dict[str, object]],
    bugs: list[dict[str, object]],
    scenario_headers: tuple[str, ...] = SCENARIO_COLUMNS,
    bug_headers: tuple[str, ...] = BUG_COLUMNS,
    blank_scenario_row: bool = False,
    blank_bug_row: bool = False,
) -> None:
    workbook = Workbook()
    scenario_sheet = workbook.active
    scenario_sheet.title = SCENARIO_SHEET
    bug_sheet = workbook.create_sheet(BUG_SHEET)
    scenario_sheet.append(list(scenario_headers))
    bug_sheet.append(list(bug_headers))
    if blank_scenario_row:
        scenario_sheet.append([None] * len(scenario_headers))
    if blank_bug_row:
        bug_sheet.append([None] * len(bug_headers))
    for row in scenarios:
        scenario_sheet.append([row.get(header) for header in scenario_headers])
    for row in bugs:
        bug_sheet.append([row.get(header) for header in bug_headers])
    workbook.save(path)
    workbook.close()


class ExcelReaderTests(unittest.TestCase):
    def test_fictitious_workbook_initial_summary(self) -> None:
        data = read_qa_workbook(TEST_WORKBOOK)
        validation = validate_qa_data(data)
        summary = summarize_qa(validation)

        self.assertEqual(summary.total_scenarios_registered, 12)
        self.assertEqual(summary.scenario_result_counts, {"Passou": 4, "Falhou": 3, "Bloqueado": 2, "Não Executado": 3})
        self.assertEqual(summary.scenario_result_denominator, 12)
        self.assertEqual(summary.scenario_result_percentages, {"Passou": 33.33, "Falhou": 25.0, "Bloqueado": 16.67, "Não Executado": 25.0})
        self.assertEqual(summary.distinct_bug_count, 4)
        self.assertEqual(summary.bug_severity_counts, {"Crítica": 1, "Alta": 1, "Média": 1, "Baixa": 1})
        self.assertEqual(summary.bug_status_counts, {"Aberto": 1, "Em Análise": 1, "Em Correção": 1, "Pronto para Reteste": 1, "Reaberto": 0, "Fechado": 0})
        self.assertEqual(validation.invalid_scenario_rows, 0)
        self.assertEqual(validation.invalid_bug_rows, 0)
        self.assertFalse(validation.issues)

    def test_headers_are_mapped_by_name_and_empty_rows_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reordered.xlsx"
            write_workbook(
                path,
                [scenario()],
                [bug()],
                scenario_headers=tuple(reversed(SCENARIO_COLUMNS)),
                bug_headers=BUG_COLUMNS[3:] + BUG_COLUMNS[:3],
                blank_scenario_row=True,
                blank_bug_row=True,
            )
            data = read_qa_workbook(path)

        self.assertEqual(len(data.scenarios), 1)
        self.assertEqual(data.scenarios[0].row_number, 3)
        self.assertEqual(data.scenarios[0].values["ID"], "TC-UNIT-01")
        self.assertEqual(data.bugs[0].values["ID do Bug"], "BUG-UNIT-01")
        self.assertEqual(data.bugs[0].row_number, 3)

    def test_duplicate_scenario_ids_are_excluded_from_outcome_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate-scenarios.xlsx"
            write_workbook(path, [scenario(), scenario(**{"Resultado": "Falhou"})], [])
            validation = validate_qa_data(read_qa_workbook(path))
            summary = summarize_qa(validation)

        duplicate_issues = [issue for issue in validation.issues if issue.field == "ID" and "duplicado" in issue.message]
        self.assertEqual(len(duplicate_issues), 2)
        self.assertEqual(summary.total_scenarios_registered, 2)
        self.assertEqual(summary.scenario_result_denominator, 0)
        self.assertEqual(summary.scenarios_excluded_from_result_denominator, 2)
        self.assertEqual(validation.invalid_scenario_rows, 2)

    def test_invalid_and_missing_results_are_not_counted_as_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid-results.xlsx"
            write_workbook(path, [scenario(**{"Resultado": "Aprovado"}), scenario(ID="TC-UNIT-02", **{"Resultado": None})], [])
            data = read_qa_workbook(path)
            validation = validate_qa_data(data)
            summary = summarize_qa(validation)
            report = format_report(data.source_path, summary, validation.issues)

        self.assertEqual(summary.scenario_result_counts["Passou"], 0)
        self.assertEqual(summary.scenario_result_denominator, 0)
        self.assertEqual(summary.scenarios_without_valid_result, 2)
        self.assertEqual(summary.invalid_scenario_rows, 2)
        self.assertIn("Aba 'Cenarios de Teste', linha 2", report)
        self.assertIn("Aba 'Cenarios de Teste', linha 3", report)

    def test_missing_optional_values_are_warnings_not_blocking_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing-optional.xlsx"
            incomplete = scenario(**{
                "US (User Story)": None,
                "Pré-condições": None,
                "Passo a passo": None,
                "Resultado esperado": None,
                "Resultado obtido": None,
                "Responsável": None,
            })
            write_workbook(path, [incomplete], [])
            validation = validate_qa_data(read_qa_workbook(path))
            summary = summarize_qa(validation)

        self.assertEqual(summary.valid_scenario_rows, 1)
        self.assertEqual(summary.scenario_result_denominator, 1)
        self.assertTrue(any(issue.level == "warning" and issue.field == "Resultado obtido" for issue in validation.issues))
        self.assertFalse(any(issue.level == "error" for issue in validation.issues))

    def test_duplicate_bug_ids_are_not_double_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate-bugs.xlsx"
            write_workbook(path, [scenario()], [bug(), bug(**{"Título": "Outro registro sintético"})])
            validation = validate_qa_data(read_qa_workbook(path))
            summary = summarize_qa(validation)

        duplicate_issues = [issue for issue in validation.issues if issue.field == "ID do Bug" and "duplicado" in issue.message]
        self.assertEqual(len(duplicate_issues), 2)
        self.assertEqual(summary.distinct_bug_count, 0)
        self.assertEqual(summary.invalid_bug_rows, 2)
        self.assertEqual(sum(summary.bug_severity_counts.values()), 0)

    def test_invalid_bug_category_is_visible_without_losing_unique_bug_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid-bug-status.xlsx"
            write_workbook(path, [scenario()], [bug(**{"Status": "Em Desenvolvimento"})])
            validation = validate_qa_data(read_qa_workbook(path))
            summary = summarize_qa(validation)

        self.assertEqual(summary.distinct_bug_count, 1)
        self.assertEqual(summary.invalid_bug_rows, 1)
        self.assertEqual(summary.bugs_without_valid_status, 1)
        self.assertEqual(sum(summary.bug_status_counts.values()), 0)
        self.assertTrue(any(issue.field == "Status" and issue.level == "error" for issue in validation.issues))

    def test_missing_required_id_and_scenario_reference_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing-ids.xlsx"
            write_workbook(
                path,
                [scenario(ID=None)],
                [bug(**{"ID do Bug": None, "ID do Cenário": "TC-UNKNOWN"})],
            )
            validation = validate_qa_data(read_qa_workbook(path))
            summary = summarize_qa(validation)

        self.assertEqual(summary.scenario_result_denominator, 0)
        self.assertEqual(summary.distinct_bug_count, 0)
        self.assertTrue(any(issue.sheet == SCENARIO_SHEET and issue.field == "ID" for issue in validation.issues))
        self.assertTrue(any(issue.sheet == BUG_SHEET and issue.field == "ID do Bug" for issue in validation.issues))
        self.assertTrue(any(issue.sheet == BUG_SHEET and issue.field == "ID do Cenário" for issue in validation.issues))


if __name__ == "__main__":
    unittest.main()
