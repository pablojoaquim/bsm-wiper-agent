import re
import subprocess
from pathlib import Path

import yaml

import main
from process_evidence import write_process_evidence


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


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_workflow_reuses_artifacts_generates_code_and_reports_evidence_gaps(
    tmp_path,
    monkeypatch,
):
    processes_path = tmp_path / "processes"
    write_yaml(
        processes_path
        / "SYS.2_system_requirements_analysis"
        / "SYS.2_system_requirements.yaml",
        {"requirements": [make_requirement("SYS-001", "system")]},
    )
    write_yaml(
        processes_path
        / "SWE.1_software_requirements_analysis"
        / "SWE.1_software_requirements.yaml",
        {"requirements": [make_requirement("SWE-001", "software")]},
    )
    write_yaml(
        processes_path
        / "SWE.2_software_architectural_design"
        / "SWE.2_software_architecture.yaml",
        {"architecture": {"components": [], "interfaces": []}},
    )
    write_yaml(
        processes_path
        / "SWE.3_software_detailed_design"
        / "SWE.3_software_detailed_design.yaml",
        {"software_detailed_design": {"units": []}},
    )
    model_path = (
        processes_path
        / "SWE.3_software_detailed_design"
        / "models"
        / "BSMWiperController.mo"
    )
    model_path.parent.mkdir(parents=True)
    model_path.write_text(
        "model BSMWiperController\n"
        "  input Boolean ignitionOn;\n"
        "  output Boolean motorOn;\n"
        "equation\n"
        "  motorOn = ignitionOn;\n"
        "end BSMWiperController;\n",
        encoding="utf-8",
    )
    test_model_path = model_path.with_name("BSMWiperTest.mo")
    test_model_path.write_text(
        "model BSMWiperTest\n"
        "  BSMWiperController controller;\n"
        "equation\n"
        "  controller.ignitionOn = true;\n"
        "  assert(controller.motorOn, \"Ignition enables motor.\");\n"
        "end BSMWiperTest;\n",
        encoding="utf-8",
    )
    write_process_evidence(
        model_path,
        stage="SWE.3 Model Generation",
        metadata={
            "model_files": [model_path.name, test_model_path.name],
            "unit_models": [],
        },
    )

    def fake_run(command, **kwargs):
        if command[1] == "--version":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="OpenModelica test version",
                stderr="",
            )
        script = open(command[1], encoding="utf-8").read()
        match = re.search(
            r'translateModel\(BSMWiperController, fileNamePrefix="([^"]+)"',
            script,
        )
        assert match is not None
        assert "simulate(BSMWiperTest" in script
        with open(f"{match.group(1)}.c", "w", encoding="utf-8") as file:
            file.write("/* generated simulation source */\n")
        with open(
            f"{Path(match.group(1)).parent / 'BSMWiperTest_res.mat'}",
            "wb",
        ) as file:
            file.write(b"simulation result")
        return subprocess.CompletedProcess(command, 0, "true\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agents.code_generation_agent.shutil.which",
        lambda _: "omc-test",
    )

    result = main.run_workflow(tmp_path, omc_executable="omc-test")

    assert result["status"] == "completed_with_evidence_gaps"
    assert result["stages"] == {
        "SYS.2": "passed",
        "SWE.1": "reused",
        "SWE.2": "reused",
        "SWE.3_design": "reused",
        "SWE.3_model": "reused",
        "SWE.3_code": "passed",
    }
    assert result["rar_summary"]["evidence_gap_count"] == 3
    rar_path = tmp_path / "processes" / "RAR_requirements_analysis_report" / "RAR.yaml"
    rar = yaml.safe_load(rar_path.read_text(encoding="utf-8"))["rar"]
    assert any(gap["evidence_path"].endswith("SWE.1_software_requirements_evidence.yaml") for gap in rar["evidence_gaps"])
    assert any(stage["stage"] == "SWE.3 Modelica Code Generation" for stage in rar["stages"])
    assert (
        processes_path
        / "SWE.3_software_detailed_design"
        / "generated"
        / "simulation_c"
        / "BSMWiperController.c"
    ).is_file()
    assert (
        processes_path
        / "SWE.3_software_detailed_design"
        / "generated"
        / "simulation_c"
        / "BSMWiperTest_res.mat"
    ).is_file()
