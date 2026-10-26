"""CLI manual para extrair texto de documentos de projeto."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.connectors.document_reader import DocumentReadError, read_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extrai texto local de documentos Markdown, PDF e DOCX."
    )
    parser.add_argument("--input", required=True, type=Path, help="Caminho de um documento.")
    args = parser.parse_args(argv)

    try:
        document = read_document(args.input)
    except DocumentReadError as exc:
        print(f"Erro de leitura: {exc}", file=sys.stderr)
        return 2

    print(f"Fonte: {document.source_path}")
    print(f"Formato: {document.format}")
    print("Conteúdo extraído:")
    print(document.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
