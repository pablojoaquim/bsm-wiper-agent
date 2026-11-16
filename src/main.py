import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.RAR_report_agent import generate_rar_report
from agents.SWE1_software_requirements_agent import generate_software_requirements
from agents.SWE2_software_architecture_agent import generate_software_architecture
from agents.SWE3_modelica_model_agent import generate_modelica_model
from agents.SWE3_software_design_agent import generate_software_design
from agents.code_generation_agent import generate_simulation_code
from process_evidence import evidence_path_for, write_process_evidence
from requirement_loader import load_requirements
from requirement_validator import validate_requirements


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_workflow(
    project_root: str | Path = PROJECT_ROOT,
    model=None,
    omc_executable: str | Path | None = None,
) -> dict:
    project_root = Path(project_root).resolve()
    processes_path = project_root / "processes"
    system_path = (
        processes_path
        / "SYS.2_system_requirements_analysis"
        / "SYS.2_system_requirements.yaml"
    )
    software_path = (
        processes_path
        / "SWE.1_software_requirements_analysis"
        / "SWE.1_software_requirements.yaml"
    )
    architecture_path = (
        processes_path
        / "SWE.2_software_architectural_design"
        / "SWE.2_software_architecture.yaml"
    )
    design_path = (
        processes_path
        / "SWE.3_software_detailed_design"
        / "SWE.3_software_detailed_design.yaml"
    )
    model_path = (
        processes_path
        / "SWE.3_software_detailed_design"
        / "models"
        / "BSMWiperController.mo"
    )
    code_output_path = (
        processes_path
        / "SWE.3_software_detailed_design"
        / "generated"
        / "simulation_c"
    )
    code_artifact_path = code_output_path / f"{model_path.stem}.c"
    rar_path = (
        processes_path
        / "RAR_requirements_analysis_report"
        / "RAR.yaml"
    )
    evidence_paths = [
        evidence_path_for(path)
        for path in (
            system_path,
            software_path,
            architecture_path,
            design_path,
            model_path,
            code_artifact_path,
        )
    ]
    stage_status = {}

    def finish() -> dict:
        rar = generate_rar_report(evidence_paths, rar_path)
        status = (
            "failed"
            if "failed" in stage_status.values()
            else "completed_with_evidence_gaps"
            if rar["rar"]["summary"]["evidence_gap_count"]
            else "completed"
        )
        return {
            "status": status,
            "stages": stage_status,
            "rar_path": str(rar_path),
            "rar_summary": rar["rar"]["summary"],
        }

    def record_failure(stage: str, artifact_path: Path, error: Exception) -> None:
        stage_status[stage] = "failed"
        write_process_evidence(
            artifact_path,
            stage=stage,
            status="failed",
            validation="Stage did not complete.",
            error=str(error),
        )

    current_model = model

    def get_model():
        nonlocal current_model
        if current_model is None:
            load_dotenv(project_root / ".env")
            model_name = os.getenv("GEMINI_MODEL")
            api_key = os.getenv("GOOGLE_API_KEY")
            if not model_name or not api_key:
                raise ValueError(
                    "Set GEMINI_MODEL and GOOGLE_API_KEY in the project .env "
                    "before generating missing AI artifacts."
                )
            current_model = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.2,
            )
        return current_model

    try:
        system_document = load_requirements(system_path)
        validation_errors = validate_requirements(system_document)
        write_process_evidence(
            system_path,
            stage="SYS.2 System Requirements Analysis",
            status="failed" if validation_errors else "passed",
            validation="Structural requirement validation completed.",
            metadata={"validation_errors": validation_errors},
            error="; ".join(validation_errors) if validation_errors else None,
            known_requirement_ids={
                requirement.id for requirement in system_document.requirements
            },
        )
        stage_status["SYS.2"] = "failed" if validation_errors else "passed"
        if validation_errors:
            return finish()
    except Exception as error:
        record_failure("SYS.2", system_path, error)
        return finish()

    try:
        if software_path.is_file():
            software_document = load_requirements(software_path)
            stage_status["SWE.1"] = "reused"
        else:
            software_document = generate_software_requirements(
                system_document,
                get_model(),
                software_path,
            )
            stage_status["SWE.1"] = "generated"
    except Exception as error:
        record_failure("SWE.1", software_path, error)
        return finish()

    try:
        if architecture_path.is_file():
            architecture = _load_yaml(architecture_path)
            stage_status["SWE.2"] = "reused"
        else:
            architecture = generate_software_architecture(
                system_document,
                software_document,
                get_model(),
                architecture_path,
            )
            stage_status["SWE.2"] = "generated"
    except Exception as error:
        record_failure("SWE.2", architecture_path, error)
        return finish()

    try:
        if design_path.is_file():
            design = _load_yaml(design_path)
            stage_status["SWE.3_design"] = "reused"
        else:
            design = generate_software_design(
                software_document,
                architecture,
                get_model(),
                design_path,
            )
            stage_status["SWE.3_design"] = "generated"
    except Exception as error:
        record_failure("SWE.3_design", design_path, error)
        return finish()

    try:
        if model_path.is_file():
            stage_status["SWE.3_model"] = "reused"
        else:
            generate_modelica_model(
                system_document,
                software_document,
                design,
                get_model(),
                model_path,
            )
            stage_status["SWE.3_model"] = "generated"
    except Exception as error:
        record_failure("SWE.3_model", model_path, error)
        return finish()

    try:
        generate_simulation_code(
            model_path,
            code_output_path,
            model_generation_record_path=evidence_path_for(model_path),
            omc_executable=omc_executable,
        )
        stage_status["SWE.3_code"] = "passed"
    except Exception:
        stage_status["SWE.3_code"] = "failed"

    return finish()


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> dict:
    result = run_workflow()
    print(f"Workflow status: {result['status']}")
    for stage, status in result["stages"].items():
        print(f"{stage}: {status}")
    print(f"RAR: {result['rar_path']}")
    print(f"RAR summary: {result['rar_summary']}")
    return result


if __name__ == "__main__":
    workflow_result = main()
    if workflow_result["status"] == "failed":
        raise SystemExit(1)