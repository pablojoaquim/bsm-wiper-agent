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
            source = {
                "stage": record.stage,
                "artifact_path": record.artifact_path,
                "evidence_path": str(evidence_path),
            }
            assumption_data = assumption.model_dump(mode="json")
            duplicate = next((
                item for item in assumptions
                if item["id"] == assumption.id
                and item["requirement_ids"] == assumption_data["requirement_ids"]
                and item["decision"] == assumption.decision
            ), None)
            if duplicate is None:
                assumptions.append({
                    **assumption_data,
                    "global_id": f"{record.stage}:{assumption.id}",
                    "sources": [source],
                })
            else:
                duplicate["sources"].append(source)

        for issue in record.open_issues:
            source = {
                "stage": record.stage,
                "artifact_path": record.artifact_path,
                "evidence_path": str(evidence_path),
            }
            issue_data = issue.model_dump(mode="json")
            duplicate = next((
                item for item in open_issues
                if item["id"] == issue.id
                and item["requirement_ids"] == issue_data["requirement_ids"]
                and item["missing_information"] == issue.missing_information
                and item["reason_unresolved"] == issue.reason_unresolved
            ), None)
            if duplicate is None:
                open_issues.append({
                    **issue_data,
                    "global_id": f"{record.stage}:{issue.id}",
                    "sources": [source],
                })
            else:
                duplicate["sources"].append(source)

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