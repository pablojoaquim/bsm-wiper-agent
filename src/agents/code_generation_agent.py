import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml


def generate_simulation_code(
    model_path: str | Path,
    output_directory: str | Path,
    model_generation_record_path: str | Path | None = None,
    omc_executable: str | Path | None = None,
    timeout: int = 300,
) -> dict:
    model_path = Path(model_path).resolve()
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    record_path = output_directory / f"{model_path.stem}_code_generation_record.yaml"
    record = {
        "stage": "SWE.3 Modelica Code Generation",
        "status": "running",
        "model_source": str(model_path),
        "compiler_executable": None,
        "compiler_version": None,
        "generated_files": [],
        "assumptions": [],
        "open_issues": [],
        "compiler_stdout": "",
        "compiler_stderr": "",
        "scope": "OpenModelica-generated C simulation code; generated C is not compiled or certified as production ECU software.",
    }

    try:
        if not model_path.is_file():
            raise FileNotFoundError(f"Modelica source not found: {model_path}")

        source_text = model_path.read_text(encoding="utf-8")
        generation_record_path = (
            Path(model_generation_record_path)
            if model_generation_record_path is not None
            else model_path.with_name(
                f"{model_path.stem}_generation_record.yaml"
            )
        )
        if generation_record_path.is_file():
            generation_record = yaml.safe_load(
                generation_record_path.read_text(encoding="utf-8")
            ) or {}
            assumptions = generation_record.get("assumptions", [])
            open_issues = generation_record.get("open_issues", [])
            if not isinstance(assumptions, list) or not isinstance(open_issues, list):
                raise ValueError("Model generation record must contain assumptions and open_issues lists.")
            assumption_markers = set(re.findall(
                r"//\s*ASSUMPTION\s+(ASM-\d+)\b",
                source_text,
                re.IGNORECASE,
            ))
            for assumption in assumptions:
                assumption_id = assumption.get("id")
                if assumption_id not in assumption_markers:
                    raise ValueError(
                        f"Modelica source does not identify assumption {assumption_id}."
                    )
            record["model_generation_record"] = str(generation_record_path)
            record["assumptions"] = assumptions
            record["open_issues"] = open_issues
        elif re.search(r"//\s*ASSUMPTION\s+ASM-\d+\b", source_text, re.IGNORECASE):
            raise ValueError(
                "Modelica source contains assumptions but its generation record is missing."
            )

        omc_path = _resolve_omc(omc_executable)
        record["compiler_executable"] = omc_path
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
        record["compiler_version"] = (
            version_result.stdout.strip() or version_result.stderr.strip()
        )

        with tempfile.TemporaryDirectory(prefix="bsm_modelica_codegen_") as temp_dir:
            temp_root = Path(temp_dir)
            temp_output = temp_root / "generated"
            temp_output.mkdir()
            modelica_script = temp_root / "generate_simulation_code.mos"
            output_prefix = temp_output / model_path.stem
            modelica_script.write_text(
                "\n".join([
                    f"loadFile({json.dumps(model_path.as_posix())});",
                    "getErrorString();",
                    "translateModel(BSMWiperController, fileNamePrefix="
                    f"{json.dumps(output_prefix.as_posix())});",
                    "getErrorString();",
                    "",
                ]),
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
            record["compiler_stdout"] = _as_text(result.stdout)
            record["compiler_stderr"] = _as_text(result.stderr)
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenModelica exited with status {result.returncode}."
                )

            generated_c = temp_output / f"{model_path.stem}.c"
            if not generated_c.is_file() or generated_c.stat().st_size == 0:
                raise RuntimeError(
                    "OpenModelica did not produce the expected C simulation source."
                )

            generated_files = sorted(
                path for path in temp_output.rglob("*") if path.is_file()
            )
            for generated_file in generated_files:
                relative_path = generated_file.relative_to(temp_output)
                destination = output_directory / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(generated_file, destination)
            record["generated_files"] = [
                str(path.relative_to(temp_output)).replace("\\", "/")
                for path in generated_files
            ]

        record["status"] = "passed"
        record["validation"] = "OpenModelica translation succeeded and non-empty C simulation source was generated."
    except Exception as error:
        record["status"] = "failed"
        record["error"] = str(error)
        _write_record(record_path, record)
        raise

    _write_record(record_path, record)
    return record


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


def _write_record(record_path: Path, record: dict) -> None:
    with record_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(record, file, sort_keys=False, allow_unicode=True)


def _as_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""