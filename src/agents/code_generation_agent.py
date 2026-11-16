import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from process_evidence import ProcessEvidence, evidence_path_for, write_process_evidence


def generate_simulation_code(
    model_path: str | Path,
    output_directory: str | Path,
    model_generation_record_path: str | Path | None = None,
    test_model_path: str | Path | None = None,
    omc_executable: str | Path | None = None,
    timeout: int = 300,
) -> dict:
    model_path = Path(model_path).resolve()
    test_model_path = (
        Path(test_model_path).resolve()
        if test_model_path is not None
        else None
    )
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    code_artifact_path = output_directory / f"{model_path.stem}.c"
    record_path = evidence_path_for(code_artifact_path)
    assumptions = []
    open_issues = []
    metadata = {
        "model_source": str(model_path),
        "test_model_source": str(test_model_path) if test_model_path else None,
        "compiler_executable": None,
        "compiler_version": None,
        "generated_files": [],
        "compiler_stdout": "",
        "compiler_stderr": "",
        "scope": "OpenModelica-generated C simulation code; generated C is not compiled or certified as production ECU software.",
    }
    status = "completed"
    validation = None

    try:
        if not model_path.is_file():
            raise FileNotFoundError(f"Modelica source not found: {model_path}")

        source_text = model_path.read_text(encoding="utf-8")
        if test_model_path is not None and not test_model_path.is_file():
            raise FileNotFoundError(f"Modelica test source not found: {test_model_path}")
        generation_record_path = (
            Path(model_generation_record_path)
            if model_generation_record_path is not None
            else model_path.with_name(
                f"{model_path.stem}_evidence.yaml"
            )
        )
        if generation_record_path.is_file():
            generation_record = ProcessEvidence.model_validate(yaml.safe_load(
                generation_record_path.read_text(encoding="utf-8")
            ) or {})
            assumptions = [
                assumption.model_dump(mode="json")
                for assumption in generation_record.assumptions
            ]
            open_issues = [
                issue.model_dump(mode="json")
                for issue in generation_record.open_issues
            ]
            assumption_markers = set(re.findall(
                r"//\s*ASSUMPTION\s+([A-Za-z0-9_-]+)\b",
                source_text,
                re.IGNORECASE,
            ))
            for assumption in assumptions:
                assumption_id = assumption.get("id")
                if assumption_id not in assumption_markers:
                    raise ValueError(
                        f"Modelica source does not identify assumption {assumption_id}."
                    )
            metadata["model_generation_evidence"] = str(generation_record_path)
        elif re.search(r"//\s*ASSUMPTION\s+[A-Za-z0-9_-]+\b", source_text, re.IGNORECASE):
            raise ValueError(
                "Modelica source contains assumptions but its generation record is missing."
            )

        omc_path = _resolve_omc(omc_executable)
        metadata["compiler_executable"] = omc_path
        version_result = subprocess.run(
            [omc_path, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if version_result.returncode != 0:
            raise RuntimeError(
                "Could not query OpenModelica version: "
                f"{version_result.stderr.strip()}"
            )
        metadata["compiler_version"] = (
            version_result.stdout.strip() or version_result.stderr.strip()
        )

        with tempfile.TemporaryDirectory(prefix="bsm_modelica_codegen_") as temp_dir:
            temp_root = Path(temp_dir)
            temp_output = temp_root / "generated"
            temp_output.mkdir()
            modelica_script = temp_root / "generate_simulation_code.mos"
            output_prefix = temp_output / model_path.stem
            script_lines = [
                f"cd({json.dumps(temp_output.as_posix())});",
                f"loadFile({json.dumps(model_path.as_posix())});",
                "getErrorString();",
            ]
            if test_model_path is not None:
                script_lines.extend([
                    f"loadFile({json.dumps(test_model_path.as_posix())});",
                    "getErrorString();",
                    "checkModel(BSMWiperTest);",
                    "getErrorString();",
                    "simulate(BSMWiperTest, stopTime=10.0);",
                    "getErrorString();",
                ])
            script_lines.extend([
                "translateModel(BSMWiperController, fileNamePrefix="
                f"{json.dumps(output_prefix.as_posix())});",
                "getErrorString();",
                "",
            ])
            modelica_script.write_text(
                "\n".join(script_lines),
                encoding="utf-8",
            )
            result = subprocess.run(
                [omc_path, str(modelica_script)],
                cwd=str(model_path.parent),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            metadata["compiler_stdout"] = _as_text(result.stdout)
            metadata["compiler_stderr"] = _as_text(result.stderr)
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenModelica exited with status {result.returncode}."
                )

            generated_c = temp_output / f"{model_path.stem}.c"
            if not generated_c.is_file() or generated_c.stat().st_size == 0:
                raise RuntimeError(
                    "OpenModelica did not produce the expected C simulation source."
                )
            if test_model_path is not None and not any(
                path.name.endswith("_res.mat")
                for path in temp_output.iterdir()
            ):
                raise RuntimeError(
                    "OpenModelica did not produce a test simulation result."
                )

            generated_files = sorted(
                path for path in temp_output.rglob("*") if path.is_file()
            )
            for generated_file in generated_files:
                relative_path = generated_file.relative_to(temp_output)
                destination = output_directory / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(generated_file, destination)
            metadata["generated_files"] = [
                str(path.relative_to(temp_output)).replace("\\", "/")
                for path in generated_files
            ]

        status = "passed"
        validation = (
            "OpenModelica simulated the test model and generated non-empty C simulation source."
            if test_model_path is not None
            else "OpenModelica translation succeeded and non-empty C simulation source was generated."
        )
    except Exception as error:
        write_process_evidence(
            code_artifact_path,
            stage="SWE.3 Modelica Code Generation",
            assumptions=assumptions,
            open_issues=open_issues,
            status="failed",
            metadata=metadata,
            error=str(error),
            evidence_path=record_path,
        )
        raise

    record, _ = write_process_evidence(
        code_artifact_path,
        stage="SWE.3 Modelica Code Generation",
        assumptions=assumptions,
        open_issues=open_issues,
        status=status,
        validation=validation,
        metadata=metadata,
        evidence_path=record_path,
    )
    return record.model_dump(mode="json", exclude_none=True)


def _resolve_omc(omc_executable: str | Path | None) -> str:
    candidate = (
        str(omc_executable)
        if omc_executable is not None
        else os.environ.get("OPENMODELICA_OMC")
    )
    resolved = shutil.which(candidate or "omc")
    if resolved is None and candidate is not None and Path(candidate).is_file():
        resolved = str(Path(candidate).resolve())
    if resolved is None:
        raise FileNotFoundError(
            "OpenModelica compiler not found. Pass omc_executable, set "
            "OPENMODELICA_OMC, or add omc to PATH."
        )
    return str(Path(resolved).resolve())


def _as_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""