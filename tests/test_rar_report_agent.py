import yaml
import pytest

from agents.RAR_report_agent import generate_rar_report
from process_evidence import write_process_evidence


def test_rar_consolidates_assumptions_open_issues_and_stage_sources(tmp_path):
    evidence_path = tmp_path / "SWE3_evidence.yaml"
    write_process_evidence(
        artifact_path="design.yaml",
        stage="SWE.3 Model Generation",
        assumptions=[{
            "id": "ASM-001",
            "requirement_ids": ["SYS-001", "SWE-001"],
            "missing_information": "Timing is unspecified.",
            "decision": "Use a one-second interval.",
            "rationale": "Provides a concrete simulation default.",
        }],
        open_issues=[{
            "id": "OI-001",
            "requirement_ids": ["SYS-001"],
            "missing_information": "Customer response-time target.",
            "reason_unresolved": "No customer target was provided.",
        }],
        validation="Model generated.",
        evidence_path=evidence_path,
    )
    output_path = tmp_path / "RAR.yaml"

    report = generate_rar_report([evidence_path], output_path)

    rar = report["rar"]
    assert rar["assumptions"][0]["classification"] == "assumption"
    assert rar["assumptions"][0]["global_id"] == "SWE.3 Model Generation:ASM-001"
    assert rar["open_issues"][0]["global_id"] == "SWE.3 Model Generation:OI-001"
    assert rar["summary"]["stage_count"] == 1
    assert yaml.safe_load(output_path.read_text(encoding="utf-8")) == report


def test_rar_reports_missing_stage_evidence_without_inventing_decisions(tmp_path):
    report = generate_rar_report(
        [tmp_path / "missing_evidence.yaml"],
        tmp_path / "RAR.yaml",
    )

    rar = report["rar"]
    assert rar["assumptions"] == []
    assert rar["open_issues"] == []
    assert rar["evidence_gaps"][0]["status"] == "missing"


def test_process_evidence_rejects_unknown_requirement_references(tmp_path):
    with pytest.raises(ValueError, match="references unknown requirements"):
        write_process_evidence(
            artifact_path="design.yaml",
            stage="SWE.3 Software Detailed Design",
            assumptions=[{
                "id": "ASM-001",
                "requirement_ids": ["SWE-999"],
                "missing_information": "Timing is unspecified.",
                "decision": "Use a one-second interval.",
                "rationale": "Provides a concrete simulation default.",
            }],
            known_requirement_ids={"SYS-001", "SWE-001"},
            evidence_path=tmp_path / "evidence.yaml",
        )