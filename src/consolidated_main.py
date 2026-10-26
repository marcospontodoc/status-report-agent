"""CLI local para consolidar Excel de QA e documentação do projeto."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.analysis.qa_analysis import analyze_qa_sources, format_analysis
from src.analysis.qa_summary import summarize_qa
from src.connectors.document_reader import DocumentReadError, read_document
from src.connectors.excel_reader import ExcelReadError, read_qa_workbook
from src.main import format_report as format_excel_report
from src.normalization.qa_data import validate_qa_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Consolida métricas de QA e relações explícitas com documentação local."
    )
    parser.add_argument("--excel", required=True, type=Path, help="Planilha local de QA (.xlsx).")
    parser.add_argument(
        "--document", required=True, nargs="+", type=Path,
        help="Um ou mais documentos locais Markdown, PDF ou DOCX.",
    )
    args = parser.parse_args(argv)

    try:
        excel_input = read_qa_workbook(args.excel)
        documents = tuple(read_document(path) for path in args.document)
    except (ExcelReadError, DocumentReadError) as exc:
        print(f"Erro de leitura: {exc}", file=sys.stderr)
        return 2

    validation = validate_qa_data(excel_input)
    summary = summarize_qa(validation)
    analysis = analyze_qa_sources(validation, excel_input.source_path, documents)

    print(format_excel_report(excel_input.source_path, summary, validation.issues))
    print()
    print(format_analysis(analysis))
    return 1 if validation.invalid_scenario_rows or validation.invalid_bug_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
