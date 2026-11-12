
from collections import Counter

from agents.requirement_models import RequirementDocument

def validate_requirements(document: RequirementDocument) -> list[str]:
    errors = []

    requirements = document.requirements
    ids = [req.id for req in requirements]
    id_counts = Counter(ids)
    existing_ids = set(ids)

    # VAL-001: Check duplicate IDs.
    for req_id, count in id_counts.items():
        if count > 1:
            errors.append(
                f"VAL-001: Duplicate requirement ID '{req_id}' "
                f"({count} occurrences)."
            )

    # VAL-002 to VAL-005: Check relationships.
    for req in requirements:

        # VAL-002: Parent must exist.
        if req.parent is not None:
            if req.parent not in existing_ids:
                errors.append(
                    f"VAL-002: Parent '{req.parent}' of "
                    f"'{req.id}' does not exist."
                )

        # VAL-003: Derived requirements must exist.
        for source_id in req.derived_from:
            if source_id not in existing_ids:
                errors.append(
                    f"VAL-003: Source '{source_id}' referenced by "
                    f"'{req.id}' does not exist."
                )

        # VAL-004: A requirement cannot be its own parent.
        if req.parent == req.id:
            errors.append(
                f"VAL-004: Requirement '{req.id}' cannot be "
                "its own parent."
            )

        # VAL-005: Software requirements must have a system parent.
        if req.level == "software":
            if req.parent is None:
                errors.append(
                    f"VAL-005: Software requirement '{req.id}' "
                    "must have a system parent."
                )
            else:
                parent = next(
                    (item for item in requirements if item.id == req.parent),
                    None,
                )
                if parent is not None and parent.level != "system":
                    errors.append(
                        f"VAL-005: Software requirement '{req.id}' "
                        "must have a system parent."
                    )


    return errors
