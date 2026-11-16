import json

import pytest
import yaml
from langchain_core.runnables import RunnableLambda

from agents.SWE3_modelica_model_agent import generate_modelica_model
from requirement_models import RequirementDocument


def make_requirement(requirement_id, level):
    return {
        "id": requirement_id,
        "title": f"Requirement {requirement_id}",
        "level": level,
        "statement": f"The {level} shall control the wiper motor output.",
        "status": "approved",
        "priority": "high",
        "verification_method": "test",
        "parent": "SYS-001" if level == "software" else None,
        "derived_from": ["SYS-001"] if level == "software" else [],
        "rationale": "Required for wiper operation.",
    }


def make_documents():
    system_document = RequirementDocument.model_validate({
        "requirements": [make_requirement("SYS-001", "system")],
    })
    software_document = RequirementDocument.model_validate({
        "requirements": [make_requirement("SWE-001", "software")],
    })
    return system_document, software_document


def test_model_generation_records_assumptions_and_proceeds_with_open_issues(tmp_path):
    system_document, software_document = make_documents()
    generated_response = {
        "modelica_source": """model BSMWiperController
  input Boolean ignitionOn;
  output Boolean motorOn;
  // ASSUMPTION ASM-001: Use ignitionOn as the output enable condition.
equation
  motorOn = ignitionOn;
end BSMWiperController;
""",
        "assumptions": [{
            "id": "ASM-001",
            "requirement_ids": ["SYS-001", "SWE-001"],
            "missing_information": "The exact output activation timing is unspecified.",
            "decision": "Drive the output directly from the validated control condition.",
            "rationale": "This is the simplest behavior consistent with the design.",
        }],
        "open_issues": [{
            "id": "OI-001",
            "requirement_ids": ["SYS-001"],
            "missing_information": "The customer has not specified a response time.",
            "reason_unresolved": "No timing target is available to model.",
        }],
    }
    model = RunnableLambda(lambda _: json.dumps(generated_response))
    model_path = tmp_path / "models" / "BSMWiperController.mo"

    record = generate_modelica_model(
        system_document,
        software_document,
        {"software_detailed_design": {"units": []}},
        model,
        model_path,
    )

    assert model_path.is_file()
    assert "ASSUMPTION ASM-001" in model_path.read_text(encoding="utf-8")
    assert record["assumptions"][0]["classification"] == "assumption"
    assert record["open_issues"][0]["id"] == "OI-001"
    persisted_record = yaml.safe_load(
        model_path.with_name("BSMWiperController_evidence.yaml")
        .read_text(encoding="utf-8")
    )
    assert persisted_record["open_issues"]


def test_model_generation_rejects_assumption_without_model_marker(tmp_path):
    system_document, software_document = make_documents()
    generated_response = {
        "modelica_source": "model BSMWiperController\nend BSMWiperController;",
        "assumptions": [{
            "id": "ASM-001",
            "requirement_ids": ["SYS-001"],
            "missing_information": "Timing is unspecified.",
            "decision": "Use a one-second interval.",
            "rationale": "Temporary prototype value.",
        }],
        "open_issues": [],
    }
    model = RunnableLambda(lambda _: json.dumps(generated_response))

    with pytest.raises(ValueError, match="does not identify assumption"):
        generate_modelica_model(
            system_document,
            software_document,
            {"software_detailed_design": {"units": []}},
            model,
            tmp_path / "BSMWiperController.mo",
        )