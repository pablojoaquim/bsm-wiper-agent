from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^(SYS|SWE)-\d{3}$")
    title: str = Field(min_length=3)
    level: Literal["system", "software"]
    statement: str = Field(min_length=10)
    status: Literal["proposed", "approved", "rejected"]
    priority: Literal["low", "medium", "high"]
    verification_method: Literal["test", "analysis", "inspection", "demonstration"]
    parent: str | None = None
    derived_from: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=5)

class RequirementDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[Requirement] = Field(min_length=1)
