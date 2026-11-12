
from pathlib import Path

from agents.requirement_loader import load_requirements
from agents.requirement_models import RequirementDocument
from agents.requirement_validator import validate_requirements


def make_requirement(
    req_id,
    level="system",
    parent=None,
):
    return {
        "id": req_id,
        "title": f"Requirement {req_id}",
        "level": level,
        "statement": f"The system shall implement {req_id}.",
        "status": "approved",
        "priority": "high",
        "verification_method": "test",
        "parent": parent,
        "derived_from": [],
        "rationale": "Required for system operation.",
    }


def test_baseline_requirements_are_valid():
    project_root = Path(__file__).resolve().parents[1]

    document = load_requirements(
        project_root
        / "requirements"
        / "system"
        / "bsm_system_requirements.yaml"
    )

    assert validate_requirements(document) == []


def test_duplicate_ids_are_detected():
    document = RequirementDocument.model_validate({
        "requirements": [
            make_requirement("SYS-001"),
            make_requirement("SYS-001"),
        ]
    })

    errors = validate_requirements(document)

    assert any("VAL-001" in error for error in errors)


def test_missing_parent_is_detected():
    document = RequirementDocument.model_validate({
        "requirements": [
            make_requirement("SWE-001", "software", "SYS-999"),
        ]
    })

    errors = validate_requirements(document)

    assert any("VAL-002" in error for error in errors)


def test_software_requirement_without_parent_is_detected():
    document = RequirementDocument.model_validate({
        "requirements": [
            make_requirement("SWE-001", "software"),
        ]
    })

    errors = validate_requirements(document)

    assert any("VAL-005" in error for error in errors)


def test_software_requirement_with_wrong_parent_level_is_detected():
    document = RequirementDocument.model_validate({
        "requirements": [
            make_requirement("SWE-001", "software", "SWE-002"),
            make_requirement("SWE-002", "software", "SYS-001"),
            make_requirement("SYS-001"),
        ]
    })

    errors = validate_requirements(document)

    assert any("VAL-005" in error for error in errors)
