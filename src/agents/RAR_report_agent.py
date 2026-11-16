from pathlib import Path

import yaml

from process_evidence import ProcessEvidence


def generate_rar_report(
    evidence_paths: list[str | Path],
    output_path: str | Path,
) -> dict:
    stage_records = []
    assumptions = []
    open_issues = []
    evidence_gaps = []

    for evidence_path in evidence_paths:
        evidence_path = Path(evidence_path)
        if not evidence_path.is_file():
            evidence_gaps.append({
                "evidence_path": str(evidence_path),
                "status": "missing",
                "reason": "The stage has no evidence record to consolidate.",
            })
            continue

        raw_record = yaml.safe_load(evidence_path.read_text(encoding="utf-8")) or {}
        record = ProcessEvidence.model_validate(raw_record)
        stage_entry = {
            "stage": record.stage,
            "status": record.status,
            "artifact_path": record.artifact_path,
            "evidence_path": str(evidence_path),
            "validation": record.validation,
            "error": record.error,
        }
        stage_records.append(stage_entry)

        for assumption in record.assumptions:
            assumptions.append({
                **assumption.model_dump(mode="json"),
                "source_stage": record.stage,
                "source_artifact": record.artifact_path,
                "source_evidence": str(evidence_path),
                "global_id": f"{record.stage}:{assumption.id}",
            })

        for issue in record.open_issues:
            open_issues.append({
                **issue.model_dump(mode="json"),
                "source_stage": record.stage,
                "source_artifact": record.artifact_path,
                "source_evidence": str(evidence_path),
                "global_id": f"{record.stage}:{issue.id}",
            })

    report = {
        "rar": {
            "schema_version": 1,
            "stages": stage_records,
            "assumptions": assumptions,
            "open_issues": open_issues,
            "evidence_gaps": evidence_gaps,
            "summary": {
                "stage_count": len(stage_records),
                "assumption_count": len(assumptions),
                "open_issue_count": len(open_issues),
                "evidence_gap_count": len(evidence_gaps),
            },
        }
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(report, file, sort_keys=False, allow_unicode=True)

    return report