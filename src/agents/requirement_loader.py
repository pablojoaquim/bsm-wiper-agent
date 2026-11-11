from pathlib import Path
import yaml
from .requirement_models import RequirementDocument

def load_requirements(file_path: str | Path) -> RequirementDocument:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return RequirementDocument.model_validate(data)
