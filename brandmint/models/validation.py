"""
Validation models for output quality checks
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Validation result status"""
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ValidationResult(BaseModel):
    """Result of output validation"""
    skill_id: str
    status: ValidationStatus
    
    # Quality metrics
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_keys: List[str] = Field(default_factory=list)
    invalid_keys: List[str] = Field(default_factory=list)
    
    # Feedback
    feedback: str = Field(default="")
    improvement_areas: List[str] = Field(default_factory=list)
    
    # Metadata
    output_path: Optional[str] = Field(default=None)
    validated_at: Optional[str] = Field(default=None)
    attempt_number: int = Field(default=1)
    
    def is_passing(self) -> bool:
        """Check if validation passed"""
        return self.status == ValidationStatus.PASS
    
    def needs_correction(self) -> bool:
        """Check if output needs auto-correction"""
        return self.status in [ValidationStatus.FAIL, ValidationStatus.PARTIAL]
