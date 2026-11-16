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
    test_model_path: str | Path | None = None,
) -> dict:
    system_requirements_json = system_document.model_dump_json(indent=2)
    software_requirements_json = software_document.model_dump_json(indent=2)
    design_json = json.dumps(design_document, indent=2)
    unit_names = [
        unit["name"]
        for unit in design_document.get("software_detailed_design", {}).get("units", [])
    ]

    prompt_template = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You generate Modelica models for automotive software design.

            Generate a complete Modelica source file and a separate test model
            from the provided system requirements, software requirements, and
            SWE.3 detailed design.

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
                        - Define a top-level `model <unit name>` class for every listed
                            SWE.3 unit, using the exact name and spelling.
                        - Define BSMWiperController as a composition of those unit classes,
                            wiring their signals according to the design and architecture.
                        - Declare BSMWiperController public inputs without default or start
                            bindings. They are driven by BSMWiperTest or another external
                            environment and must not create overdetermined equations.
                        - Define BSMWiperTest in a separate source string. It must instantiate
                            BSMWiperController, provide deterministic input scenarios, and use
                            Modelica assert statements to check expected output behavior.
                        - Annotate each test case with its requirement IDs. If expected
                            behavior depends on an assumption, identify that assumption in the
                            test comment and evidence.
                        - Do not represent a test assumption as customer-confirmed behavior.
            - Return ONLY valid JSON, with no Markdown fences.

            Return an object with this structure:
            {{
              "modelica_source": "complete Modelica source as a JSON string",
              "test_modelica_source": "complete BSMWiperTest source as a JSON string",
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
            Generate the Modelica source and test harness from these engineering inputs.

            SYSTEM REQUIREMENTS:
            {system_requirements}

            SOFTWARE REQUIREMENTS:
            {software_requirements}

            SWE.3 DETAILED DESIGN:
            {detailed_design}

            REQUIRED TOP-LEVEL UNIT MODEL NAMES:
            {unit_model_names}
            """
        ),
    ])

    chain = prompt_template | model | StrOutputParser()
    response_text = chain.invoke({
        "system_requirements": system_requirements_json,
        "software_requirements": software_requirements_json,
        "detailed_design": design_json,
        "unit_model_names": ", ".join(unit_names),
    })
    generated = json.loads(response_text)

    modelica_source = generated.get("modelica_source")
    test_modelica_source = generated.get("test_modelica_source")
    assumptions = generated.get("assumptions")
    open_issues = generated.get("open_issues")
    if not isinstance(modelica_source, str) or not modelica_source.strip():
        raise ValueError("The model generator returned no Modelica source.")
    if not isinstance(test_modelica_source, str) or not test_modelica_source.strip():
        raise ValueError("The model generator returned no Modelica test source.")
    if not isinstance(assumptions, list) or not isinstance(open_issues, list):
        raise ValueError("The model generator must return assumptions and open_issues lists.")

    _validate_model_class(modelica_source, "BSMWiperController")
    for unit_name in unit_names:
        _validate_model_class(modelica_source, unit_name)
    _validate_model_class(test_modelica_source, "BSMWiperTest")
    if not re.search(r"\bassert\s*\(", test_modelica_source, re.IGNORECASE):
        raise ValueError("BSMWiperTest must contain executable assert statements.")

    known_requirement_ids = {
        requirement.id
        for requirement in system_document.requirements + software_document.requirements
    }
    _validate_records(assumptions, known_requirement_ids, "assumption")
    _validate_records(open_issues, known_requirement_ids, "open issue")

    combined_source = f"{modelica_source}\n{test_modelica_source}"
    for assumption in assumptions:
        marker = rf"ASSUMPTION\s+{re.escape(assumption['id'])}\b"
        if not re.search(marker, combined_source, re.IGNORECASE):
            raise ValueError(
                f"Modelica source does not identify assumption {assumption['id']}."
            )
        assumption["classification"] = "assumption"

    model_path = Path(model_path)
    test_model_path = (
        Path(test_model_path)
        if test_model_path is not None
        else model_path.with_name("BSMWiperTest.mo")
    )
    model_path.parent.mkdir(parents=True, exist_ok=True)
    test_model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(modelica_source, encoding="utf-8")
    test_model_path.write_text(test_modelica_source, encoding="utf-8")
    record, _ = write_process_evidence(
        model_path,
        stage="SWE.3 Model Generation",
        assumptions=assumptions,
        open_issues=open_issues,
        validation="Controller, unit, test-harness, and assumption-marker checks passed; compiler validation not run.",
        metadata={
            "model_files": [model_path.name, test_model_path.name],
            "unit_models": unit_names,
        },
        known_requirement_ids=known_requirement_ids,
    )

    return record.model_dump(mode="json", exclude_none=True)


def _validate_model_class(modelica_source: str, class_name: str) -> None:
    if not re.search(rf"\bmodel\s+{re.escape(class_name)}\b", modelica_source):
        raise ValueError(f"Modelica source must define {class_name}.")
    if not re.search(
        rf"\bend\s+{re.escape(class_name)}\s*;",
        modelica_source,
    ):
        raise ValueError(f"Modelica source must end {class_name} correctly.")


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