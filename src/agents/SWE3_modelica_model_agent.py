import json
import re
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from process_evidence import write_process_evidence
from requirement_models import RequirementDocument


def generate_modelica_model(
    system_document: RequirementDocument,
    software_document: RequirementDocument,
    design_document: dict,
    model,
    model_path: str | Path,
) -> dict:
    system_requirements_json = system_document.model_dump_json(indent=2)
    software_requirements_json = software_document.model_dump_json(indent=2)
    design_json = json.dumps(design_document, indent=2)

    prompt_template = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You generate Modelica models for automotive software design.

            Generate one complete Modelica model named BSMWiperController from
            the provided system requirements, software requirements, and SWE.3
            detailed design.

            Rules:
            - Continue when requirements are incomplete or ambiguous.
            - Identify missing information that affects the model.
            - Adopt a reasonable technical decision when needed to proceed.
            - Record every adopted decision as an assumption with its rationale
              and related requirement IDs.
            - Put a Modelica comment of the form
              "// ASSUMPTION ASM-001: <decision>" beside each assumed behavior.
            - Never present an assumption as customer-confirmed or change the
              source requirements.
            - Record unresolved issues separately and still produce the model.
            - Use each adopted decision in the generated model.
            - Use Modelica built-in types and valid Modelica syntax.
            - Do not add behavior unsupported by a requirement or an explicit
              assumption.
            - Return ONLY valid JSON, with no Markdown fences.

            Return an object with this structure:
            {{
              "modelica_source": "complete Modelica source as a JSON string",
              "assumptions": [
                {{
                  "id": "ASM-001",
                  "requirement_ids": ["SYS-001", "SWE-001"],
                  "missing_information": "Information needed to implement the behavior.",
                  "decision": "The technical assumption used in the model.",
                  "rationale": "Why this is a reasonable decision."
                }}
              ],
              "open_issues": [
                {{
                  "id": "OI-001",
                  "requirement_ids": ["SYS-001"],
                  "missing_information": "Information still requiring review.",
                  "reason_unresolved": "Why it remains open despite the model proceeding."
                }}
              ]
            }}
            """
        ),
        (
            "user",
            """
            Generate the Modelica model from these engineering inputs.

            SYSTEM REQUIREMENTS:
            {system_requirements}

            SOFTWARE REQUIREMENTS:
            {software_requirements}

            SWE.3 DETAILED DESIGN:
            {detailed_design}
            """
        ),
    ])

    chain = prompt_template | model | StrOutputParser()
    response_text = chain.invoke({
        "system_requirements": system_requirements_json,
        "software_requirements": software_requirements_json,
        "detailed_design": design_json,
    })
    generated = json.loads(response_text)

    modelica_source = generated.get("modelica_source")
    assumptions = generated.get("assumptions")
    open_issues = generated.get("open_issues")
    if not isinstance(modelica_source, str) or not modelica_source.strip():
        raise ValueError("The model generator returned no Modelica source.")
    if not isinstance(assumptions, list) or not isinstance(open_issues, list):
        raise ValueError("The model generator must return assumptions and open_issues lists.")
    if not re.search(r"\bmodel\s+BSMWiperController\b", modelica_source):
        raise ValueError("The Modelica source must define BSMWiperController.")
    if not re.search(r"\bend\s+BSMWiperController\s*;", modelica_source):
        raise ValueError("The Modelica source must end BSMWiperController correctly.")

    known_requirement_ids = {
        requirement.id
        for requirement in system_document.requirements + software_document.requirements
    }
    _validate_records(assumptions, known_requirement_ids, "assumption")
    _validate_records(open_issues, known_requirement_ids, "open issue")

    for assumption in assumptions:
        marker = rf"ASSUMPTION\s+{re.escape(assumption['id'])}\b"
        if not re.search(marker, modelica_source, re.IGNORECASE):
            raise ValueError(
                f"Modelica source does not identify assumption {assumption['id']}."
            )
        assumption["classification"] = "assumption"

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(modelica_source, encoding="utf-8")
    record, _ = write_process_evidence(
        model_path,
        stage="SWE.3 Model Generation",
        assumptions=assumptions,
        open_issues=open_issues,
        validation="Modelica class and assumption-marker checks passed; compiler validation not run.",
        metadata={"model_file": model_path.name},
        known_requirement_ids=known_requirement_ids,
    )

    return record.model_dump(mode="json", exclude_none=True)


def _validate_records(
    records: list,
    known_requirement_ids: set[str],
    record_type: str,
) -> None:
    required_fields = {
        "assumption": {"id", "requirement_ids", "missing_information", "decision", "rationale"},
        "open issue": {"id", "requirement_ids", "missing_information", "reason_unresolved"},
    }[record_type]

    for record in records:
        if not isinstance(record, dict) or not required_fields.issubset(record):
            raise ValueError(f"Each {record_type} must include {sorted(required_fields)}.")

        requirement_ids = record["requirement_ids"]
        if not isinstance(requirement_ids, list) or not requirement_ids:
            raise ValueError(f"Each {record_type} must reference at least one requirement.")

        unknown_ids = set(requirement_ids) - known_requirement_ids
        if unknown_ids:
            raise ValueError(
                f"{record_type.title()} {record['id']} references unknown requirements: "
                f"{', '.join(sorted(unknown_ids))}"
            )