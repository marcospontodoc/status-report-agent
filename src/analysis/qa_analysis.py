"""Análise consolidada rastreável de QA e requisitos documentados."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from src.connectors.document_reader import DocumentContent
from src.normalization.qa_data import ScenarioRecord, ValidationReport


@dataclass(frozen=True)
class SourceReference:
    source_path: Path
    location: str


@dataclass(frozen=True)
class DocumentedRequirement:
    identifier: str
    description: str
    source: SourceReference
    explicit_scenario_ids: tuple[str, ...]


@dataclass(frozen=True)
class RequirementScenarioLink:
    requirement: DocumentedRequirement
    scenario: ScenarioRecord
    basis: str


@dataclass(frozen=True)
class PossibleDivergence:
    description: str
    document_source: SourceReference
    scenario_source: SourceReference


@dataclass(frozen=True)
class PotentialRisk:
    description: str
    evidence: SourceReference


@dataclass(frozen=True)
class DocumentHypothesis:
    text: str
    source: SourceReference


@dataclass(frozen=True)
class ConsolidatedAnalysis:
    excel_source: Path
    document_sources: tuple[tuple[Path, str], ...]
    requirements: tuple[DocumentedRequirement, ...]
    links: tuple[RequirementScenarioLink, ...]
    scenarios_without_requirement: tuple[ScenarioRecord, ...]
    requirements_without_scenario: tuple[DocumentedRequirement, ...]
    unresolved_scenario_references: tuple[tuple[DocumentedRequirement, str], ...]
    possible_divergences: tuple[PossibleDivergence, ...]
    hypotheses: tuple[DocumentHypothesis, ...]
    potential_risks: tuple[PotentialRisk, ...]
    documentation_gaps: tuple[str, ...]


def _key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold().strip()


def _cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if "|" in stripped:
        return [cell.strip() for cell in stripped.strip("|").split("|")]
    if "\t" in stripped:
        return [cell.strip() for cell in stripped.split("\t")]
    return None


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _scenario_ids_in(text: str, scenario_ids: dict[str, str]) -> tuple[str, ...]:
    found: list[str] = []
    for folded_id, original_id in scenario_ids.items():
        if re.search(rf"(?<![\w-]){re.escape(original_id)}(?![\w-])", text, flags=re.IGNORECASE):
            found.append(original_id)

    # Aceita intervalos explícitos como TC-001 a TC-003 somente para IDs que
    # existem na planilha e compartilham prefixo e largura numérica.
    for match in re.finditer(
        r"([A-Za-z][A-Za-z0-9_-]*?)(\d+)\s+(?:a|até|ate|through|to|[-–])\s+([A-Za-z][A-Za-z0-9_-]*?)(\d+)",
        text,
        flags=re.IGNORECASE,
    ):
        first_prefix, first_number, last_prefix, last_number = match.groups()
        if first_prefix.casefold() != last_prefix.casefold():
            continue
        start, end = int(first_number), int(last_number)
        if end < start or end - start > 1000:
            continue
        for number in range(start, end + 1):
            candidate_id = f"{first_prefix}{number:0{len(first_number)}d}"
            if candidate_id.casefold() in scenario_ids:
                found.append(scenario_ids[candidate_id.casefold()])
    return tuple(dict.fromkeys(found))


def _extract_document_content(
    document: DocumentContent,
    known_scenario_ids: dict[str, str],
) -> tuple[list[DocumentedRequirement], list[DocumentHypothesis]]:
    lines = document.text.splitlines()
    requirements: list[DocumentedRequirement] = []
    hypotheses: list[DocumentHypothesis] = []
    in_requirement_section = False
    in_hypothesis_section = False
    header_map: dict[str, int] | None = None
    hypothesis_lines: list[str] = []
    hypothesis_start: int | None = None

    def finish_hypothesis() -> None:
        nonlocal hypothesis_lines, hypothesis_start
        content = "\n".join(line for line in hypothesis_lines if line.strip()).strip()
        if content and hypothesis_start is not None:
            hypotheses.append(
                DocumentHypothesis(
                    text=content,
                    source=SourceReference(document.source_path, f"linhas {hypothesis_start}-{hypothesis_start + len(hypothesis_lines) - 1}"),
                )
            )
        hypothesis_lines = []
        hypothesis_start = None

    for line_number, line in enumerate(lines, start=1):
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        plain_heading = line.strip().lstrip("#").strip() if heading else line.strip()
        plain_heading_key = _key(plain_heading)
        recognized_plain_heading = (
            not heading
            and "|" not in line
            and "\t" not in line
            and len(plain_heading) <= 160
            and plain_heading_key.startswith(("requisit", "requirement", "hipotese", "hypothes", "regra", "criterio", "bug", "restricao", "escopo", "objetivo"))
        )
        if heading or recognized_plain_heading:
            finish_hypothesis()
            heading_key = plain_heading_key
            in_requirement_section = "requisit" in heading_key or "requirement" in heading_key
            in_hypothesis_section = "hipotese" in heading_key or "hypothes" in heading_key
            if in_hypothesis_section:
                hypothesis_start = line_number + 1
            header_map = None
            continue

        if in_hypothesis_section:
            hypothesis_lines.append(line)
            continue
        if not in_requirement_section:
            continue

        cells = _cells(line)
        if not cells or _is_separator_row(cells):
            continue
        normalized_headers = [_key(cell) for cell in cells]
        if any(header in {"referencia", "id", "identificador", "requirement id", "requisito"} for header in normalized_headers):
            reference_index = next(
                index for index, header in enumerate(normalized_headers)
                if header in {"referencia", "id", "identificador", "requirement id", "requisito"}
            )
            description_index = next(
                (index for index, header in enumerate(normalized_headers)
                 if any(term in header for term in ("comportamento", "descricao", "description", "requirement", "criterio"))),
                None,
            )
            evidence_index = next(
                (index for index, header in enumerate(normalized_headers)
                 if any(term in header for term in ("evidencia", "cenario", "scenario", "teste", "test"))),
                None,
            )
            if description_index is not None:
                header_map = {"reference": reference_index, "description": description_index}
                if evidence_index is not None:
                    header_map["evidence"] = evidence_index
                continue
        if header_map is None or max(header_map.values()) >= len(cells):
            continue

        identifier = cells[header_map["reference"]].strip(" `")
        description = cells[header_map["description"]].strip()
        if not identifier or not description or _key(identifier) in {"referencia", "id", "identificador"}:
            continue
        evidence = cells[header_map["evidence"]] if "evidence" in header_map and header_map["evidence"] < len(cells) else ""
        explicit_ids = _scenario_ids_in(evidence, known_scenario_ids)
        requirements.append(
            DocumentedRequirement(
                identifier=identifier,
                description=description,
                source=SourceReference(document.source_path, f"linha {line_number}"),
                explicit_scenario_ids=explicit_ids,
            )
        )

    finish_hypothesis()
    return requirements, hypotheses


def analyze_qa_sources(
    validation: ValidationReport,
    excel_source: Path,
    documents: tuple[DocumentContent, ...],
) -> ConsolidatedAnalysis:
    """Relaciona apenas referências explícitas e conserva as fontes."""

    scenario_id_counts: dict[str, int] = {}
    known_scenario_ids: dict[str, str] = {}
    known_story_ids: dict[str, str] = {}
    for scenario in validation.scenarios:
        if scenario.identifier:
            key = scenario.identifier.casefold()
            scenario_id_counts[key] = scenario_id_counts.get(key, 0) + 1
            known_scenario_ids[key] = scenario.identifier
        if scenario.user_story:
            known_story_ids[scenario.user_story.casefold()] = scenario.user_story

    parsed_requirements: list[DocumentedRequirement] = []
    hypotheses: list[DocumentHypothesis] = []
    for document in documents:
        extracted, document_hypotheses = _extract_document_content(
            document, known_scenario_ids
        )
        parsed_requirements.extend(extracted)
        hypotheses.extend(document_hypotheses)

    unique_scenarios = {
        scenario.identifier.casefold(): scenario
        for scenario in validation.scenarios
        if scenario.identifier and scenario_id_counts.get(scenario.identifier.casefold()) == 1
    }
    links: list[RequirementScenarioLink] = []
    requirements_without_scenario: list[DocumentedRequirement] = []
    unresolved: list[tuple[DocumentedRequirement, str]] = []
    divergences: list[PossibleDivergence] = []
    linked_scenario_keys: set[tuple[str, int]] = set()

    for requirement in parsed_requirements:
        linked_records: dict[tuple[str, int], tuple[ScenarioRecord, str]] = {}
        matching_story = requirement.identifier.casefold()
        for scenario in validation.scenarios:
            if scenario.user_story and scenario.user_story.casefold() == matching_story:
                if scenario.identifier and scenario_id_counts.get(scenario.identifier.casefold()) == 1:
                    linked_records[(scenario.identifier.casefold(), scenario.row_number)] = (
                        scenario, f"User Story '{scenario.user_story}' coincide com a referência documentada."
                    )

        for scenario_id in requirement.explicit_scenario_ids:
            scenario_key = scenario_id.casefold()
            scenario = unique_scenarios.get(scenario_key)
            if scenario is None:
                unresolved.append((requirement, scenario_id))
                continue
            linked_records[(scenario_key, scenario.row_number)] = (
                scenario, f"ID do cenário '{scenario_id}' citado explicitamente na evidência documental."
            )
            if (
                matching_story in known_story_ids
                and scenario.user_story
                and scenario.user_story.casefold() != matching_story
            ):
                divergences.append(
                    PossibleDivergence(
                        description=(
                            f"A documentação associa '{scenario_id}' à referência '{requirement.identifier}', "
                            f"mas o Excel registra a User Story '{scenario.user_story}'. É uma divergência de referências, "
                            "não uma conclusão sobre o comportamento do sistema."
                        ),
                        document_source=requirement.source,
                        scenario_source=SourceReference(excel_source, f"aba 'Cenarios de Teste', linha {scenario.row_number}"),
                    )
                )

        if not linked_records:
            requirements_without_scenario.append(requirement)
        for (scenario_key, row_number), (scenario, basis) in linked_records.items():
            links.append(RequirementScenarioLink(requirement, scenario, basis))
            linked_scenario_keys.add((scenario_key, row_number))

    scenarios_without_requirement = tuple(
        scenario for scenario in validation.scenarios
        if not scenario.identifier
        or scenario_id_counts.get(scenario.identifier.casefold()) != 1
        or (scenario.identifier.casefold(), scenario.row_number) not in linked_scenario_keys
    )

    risks: list[PotentialRisk] = []
    for scenario in validation.scenario_outcomes:
        if scenario.result in {"Falhou", "Bloqueado", "Não Executado"}:
            if scenario.result == "Falhou":
                text = f"Possível risco de qualidade: cenário {scenario.identifier or '(sem ID)'} está registrado como Falhou; isso indica resultado adverso no teste, sem determinar por si só impacto de produção."
            elif scenario.result == "Bloqueado":
                text = f"Possível risco de validação: cenário {scenario.identifier or '(sem ID)'} está Bloqueado, limitando a evidência disponível sobre o comportamento."
            else:
                text = f"Possível lacuna de cobertura: cenário {scenario.identifier or '(sem ID)'} está Não Executado; seu resultado permanece desconhecido."
            risks.append(PotentialRisk(text, SourceReference(excel_source, f"aba 'Cenarios de Teste', linha {scenario.row_number}")))
    for bug in validation.distinct_bugs:
        if bug.status and bug.status != "Fechado":
            risks.append(
                PotentialRisk(
                    f"Possível risco de acompanhamento: bug {bug.identifier or '(sem ID)'} está registrado como '{bug.status}'. O status é evidência de pendência no fluxo, não uma medida de impacto além da severidade registrada.",
                    SourceReference(excel_source, f"aba 'Bugs', linha {bug.row_number}"),
                )
            )

    gaps: list[str] = []
    if not documents:
        gaps.append("Nenhum documento foi fornecido; relações e comparação documental não foram avaliadas.")
    elif not parsed_requirements:
        gaps.append("Nenhum requisito em estrutura identificável foi extraído; isso não prova que a documentação não contenha requisitos.")
    if unresolved:
        gaps.append("Há referências documentais a IDs de cenário ausentes ou ambíguos no Excel.")
    return ConsolidatedAnalysis(
        excel_source=excel_source,
        document_sources=tuple((document.source_path, document.format) for document in documents),
        requirements=tuple(parsed_requirements),
        links=tuple(links),
        scenarios_without_requirement=scenarios_without_requirement,
        requirements_without_scenario=tuple(requirements_without_scenario),
        unresolved_scenario_references=tuple(unresolved),
        possible_divergences=tuple(divergences),
        hypotheses=tuple(hypotheses),
        potential_risks=tuple(risks),
        documentation_gaps=tuple(gaps),
    )


def format_analysis(analysis: ConsolidatedAnalysis) -> str:
    """Apresenta relações e inferências com a origem disponível."""

    lines = ["ANÁLISE CONSOLIDADA", "", "DOCUMENTOS CONSULTADOS"]
    lines.extend(f"  {format_name}: {path}" for path, format_name in analysis.document_sources)
    if not analysis.document_sources:
        lines.append("  Nenhum.")
    lines.extend(["", "REQUISITOS DOCUMENTADOS E CENÁRIOS RELACIONADOS"])
    if not analysis.requirements:
        lines.append("  Nenhum requisito foi extraído em estrutura identificável.")
    for requirement in analysis.requirements:
        lines.append(
            f"  {requirement.identifier}: {requirement.description} "
            f"[documento: {requirement.source.source_path}; {requirement.source.location}]"
        )
        matching_links = [link for link in analysis.links if link.requirement == requirement]
        if not matching_links:
            lines.append("    Cenários relacionados: nenhum vínculo explícito encontrado.")
        for link in matching_links:
            lines.append(
                f"    Cenário {link.scenario.identifier} (aba 'Cenarios de Teste', "
                f"linha {link.scenario.row_number}; "
                f"{link.basis})"
            )

    lines.extend(["", "CENÁRIOS SEM REQUISITO RELACIONADO EXPLICITAMENTE"])
    if not analysis.scenarios_without_requirement:
        lines.append("  Nenhum.")
    for scenario in analysis.scenarios_without_requirement:
        lines.append(
            f"  {scenario.identifier or '(sem ID)'} — aba 'Cenarios de Teste', linha {scenario.row_number}; "
            "nenhuma relação explícita confirmada. Isso não prova ausência de requisito."
        )

    lines.extend(["", "REQUISITOS SEM CENÁRIO RELACIONADO EXPLICITAMENTE"])
    if not analysis.requirements_without_scenario:
        lines.append("  Nenhum.")
    for requirement in analysis.requirements_without_scenario:
        lines.append(
            f"  {requirement.identifier} — {requirement.source.source_path}, {requirement.source.location}."
        )

    lines.extend(["", "REFERÊNCIAS DOCUMENTAIS A CENÁRIOS AUSENTES OU AMBÍGUOS"])
    if not analysis.unresolved_scenario_references:
        lines.append("  Nenhuma.")
    for requirement, scenario_id in analysis.unresolved_scenario_references:
        lines.append(
            f"  {requirement.identifier} cita {scenario_id}, sem correspondência única no Excel "
            f"[{requirement.source.source_path}; {requirement.source.location}]."
        )

    lines.extend(["", "POSSÍVEIS DIVERGÊNCIAS EXPLÍCITAS DE REFERÊNCIA"])
    if not analysis.possible_divergences:
        lines.append("  Nenhuma divergência explícita de identificadores encontrada.")
    for divergence in analysis.possible_divergences:
        lines.append(
            f"  {divergence.description} Documento: {divergence.document_source.source_path}, "
            f"{divergence.document_source.location}; Excel: {divergence.scenario_source.source_path}, "
            f"{divergence.scenario_source.location}."
        )

    lines.extend(["", "HIPÓTESES IDENTIFICADAS EXPLICITAMENTE NA DOCUMENTAÇÃO"])
    if not analysis.hypotheses:
        lines.append("  Nenhuma seção rotulada como hipótese foi identificada.")
    for hypothesis in analysis.hypotheses:
        excerpt = " ".join(hypothesis.text.split())
        lines.append(f"  {excerpt} [documento: {hypothesis.source.source_path}; {hypothesis.source.location}]")

    lines.extend(["", "RISCOS POTENCIAIS (INFERÊNCIAS COM EVIDÊNCIA)"])
    if not analysis.potential_risks:
        lines.append("  Nenhum risco potencial derivado pelas regras atuais.")
    for risk in analysis.potential_risks:
        lines.append(f"  - {risk.description} [Excel: {risk.evidence.source_path}; {risk.evidence.location}]")

    lines.extend(["", "LACUNAS DA ANÁLISE DOCUMENTAL"])
    if not analysis.documentation_gaps:
        lines.append("  Nenhuma lacuna estrutural detectada para o método de relação explícita.")
    lines.extend(f"  - {gap}" for gap in analysis.documentation_gaps)
    return "\n".join(lines)
