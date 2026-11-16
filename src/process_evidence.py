from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class AssumptionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    classification: Literal["assumption"] = "assumption"
    requirement_ids: list[str] = Field(min_length=1)
    missing_information: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class OpenIssueEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: Literal["open"] = "open"
    requirement_ids: list[str] = Field(min_length=1)
    missing_information: str = Field(min_length=1)
    reason_unresolved: str = Field(min_length=1)


class ProcessEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    stage: str = Field(min_length=1)
    status: Literal["passed", "failed", "completed"] = "completed"
    artifact_path: str
    assumptions: list[AssumptionEvidence] = Field(default_factory=list)
    open_issues: list[OpenIssueEvidence] = Field(default_factory=list)
    validation: str | None = None
    metadata: dict = Field(default_factory=dict)
    error: str | None = None


def evidence_path_for(artifact_path: str | Path) -> Path:
    artifact_path = Path(artifact_path)
    return artifact_path.with_name(f"{artifact_path.stem}_evidence.yaml")


def write_process_evidence(
    artifact_path: str | Path,
    stage: str,
    assumptions: list[dict] | None = None,
    open_issues: list[dict] | None = None,
    status: Literal["passed", "failed", "completed"] = "completed",
    validation: str | None = None,
    metadata: dict | None = None,
    error: str | None = None,
    evidence_path: str | Path | None = None,
    known_requirement_ids: set[str] | None = None,
) -> tuple[ProcessEvidence, Path]:
    record = ProcessEvidence(
        stage=stage,
        status=status,
        artifact_path=str(artifact_path),
        assumptions=assumptions or [],
        open_issues=open_issues or [],
        validation=validation,
        metadata=metadata or {},
        error=error,
    )
    if known_requirement_ids is not None:
        for evidence_item in [*record.assumptions, *record.open_issues]:
            unknown_ids = set(evidence_item.requirement_ids) - known_requirement_ids
            if unknown_ids:
                raise ValueError(
                    f"Evidence {evidence_item.id} references unknown requirements: "
                    f"{', '.join(sorted(unknown_ids))}"
                )

    destination = Path(evidence_path) if evidence_path else evidence_path_for(artifact_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            record.model_dump(mode="json", exclude_none=True),
            file,
            sort_keys=False,
            allow_unicode=True,
        )
    return record, destination