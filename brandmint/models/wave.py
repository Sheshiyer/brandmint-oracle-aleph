"""
Wave models — Data structures for wave-based execution planning.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class WaveStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SkillStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SkillExecution(BaseModel):
    """Track execution state of a single skill or asset."""
    id: str
    name: str
    status: SkillStatus = Field(default=SkillStatus.PENDING)
    output_path: Optional[str] = None
    files: List[str] = Field(default_factory=list)
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class Wave(BaseModel):
    """A single execution wave containing text skills and visual assets."""
    number: int
    name: str
    description: str = ""
    text_skills: List[str] = Field(default_factory=list)
    visual_assets: List[str] = Field(default_factory=list)
    depends_on: List[int] = Field(default_factory=list)
    status: WaveStatus = Field(default=WaveStatus.PENDING)
    estimated_cost: float = 0.0
    post_hook: Optional[str] = None

    # Execution tracking
    skill_executions: Dict[str, SkillExecution] = Field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "name": self.name,
            "description": self.description,
            "text_skills": self.text_skills,
            "visual_assets": self.visual_assets,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "estimated_cost": self.estimated_cost,
        }


class WavePlan(BaseModel):
    """Complete wave execution plan for a brand."""
    brand_name: str
    scenario_id: Optional[str] = None
    depth: str = "focused"
    channel: str = "dtc"
    waves: List[Wave] = Field(default_factory=list)

    @property
    def total_text_skills(self) -> int:
        return sum(len(w.text_skills) for w in self.waves)

    @property
    def total_visual_assets(self) -> int:
        return sum(len(w.visual_assets) for w in self.waves)

    @property
    def total_cost(self) -> float:
        return sum(w.estimated_cost for w in self.waves)


class ExecutionState(BaseModel):
    """Persistent state tracking across sessions."""
    brand: str
    scenario: Optional[str] = None
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    waves: Dict[str, dict] = Field(default_factory=dict)

    def save(self, path: str):
        """Save state to JSON file."""
        import json
        with open(path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ExecutionState":
        """Load state from JSON file."""
        import json
        with open(path) as f:
            return cls.model_validate(json.load(f))
