import re
import subprocess
from pathlib import Path

import pytest
import yaml

from agents.code_generation_agent import generate_simulation_code
from process_evidence import write_process_evidence


def test_generates_simulation_code_and_preserves_assumption_evidence(
    tmp_path,
    monkeypatch,
):
    model_path = tmp_path / "models" / "BSMWiperController.mo"
    model_path.parent.mkdir()
    model_path.write_text(
        "model BSMWiperController\n"
        "  // ASSUMPTION ASM-001: Use ignition as output enable.\n"
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
        assumptions=[{
            "id": "ASM-001",
            "classification": "assumption",
            "requirement_ids": ["SYS-001"],
            "missing_information": "Timing is unspecified.",
            "decision": "Use ignition as output enable.",
            "rationale": "Simple fallback.",
        }],
        open_issues=[{
            "id": "OI-001",
            "requirement_ids": ["SYS-001"],
            "missing_information": "Timing target.",
            "reason_unresolved": "No timing target was provided.",
        }],
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
        prefix = re.search(r'translateModel\(BSMWiperController, fileNamePrefix="([^"]+)"', script)
        assert prefix is not None
        assert "simulate(BSMWiperTest" in script
        generated_c = f"{prefix.group(1)}.c"
        with open(generated_c, "w", encoding="utf-8") as file:
            file.write("/* generated simulation source */\n")
        with open(f"{prefix.group(1)}.h", "w", encoding="utf-8") as file:
            file.write("/* generated header */\n")
        with open(
            f"{Path(prefix.group(1)).parent / 'BSMWiperTest_res.mat'}",
            "wb",
        ) as file:
            file.write(b"simulation result")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="true\n\"\"\ntrue\n\"\"",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("agents.code_generation_agent.shutil.which", lambda _: "omc-test")
    output_directory = tmp_path / "simulation_c"

    record = generate_simulation_code(
        model_path,
        output_directory,
        omc_executable="omc-test",
        test_model_path=test_model_path,
    )

    assert record["status"] == "passed"
    assert record["metadata"]["compiler_version"] == "OpenModelica test version"
    assert record["assumptions"][0]["id"] == "ASM-001"
    assert record["open_issues"][0]["id"] == "OI-001"
    assert (output_directory / "BSMWiperController.c").is_file()
    assert "BSMWiperController.h" in record["metadata"]["generated_files"]
    assert "BSMWiperTest_res.mat" in record["metadata"]["generated_files"]

    persisted_record = yaml.safe_load(
        (output_directory / "BSMWiperController_evidence.yaml")
        .read_text(encoding="utf-8")
    )
    assert persisted_record["metadata"]["compiler_stdout"].startswith("true")


def test_records_translation_failure_and_does_not_report_success(tmp_path, monkeypatch):
    model_path = tmp_path / "BSMWiperController.mo"
    model_path.write_text(
        "model BSMWiperController\nend BSMWiperController;\n",
        encoding="utf-8",
    )

    def fake_run(command, **kwargs):
        if command[1] == "--version":
            return subprocess.CompletedProcess(command, 0, "OpenModelica test", "")
        return subprocess.CompletedProcess(command, 0, "false\n", "translation failed")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("agents.code_generation_agent.shutil.which", lambda _: "omc-test")
    output_directory = tmp_path / "simulation_c"

    with pytest.raises(RuntimeError, match="did not produce the expected C"):
        generate_simulation_code(
            model_path,
            output_directory,
            omc_executable="omc-test",
        )

    persisted_record = yaml.safe_load(
        (output_directory / "BSMWiperController_evidence.yaml")
        .read_text(encoding="utf-8")
    )
    assert persisted_record["status"] == "failed"
    assert persisted_record["metadata"]["compiler_stderr"] == "translation failed"