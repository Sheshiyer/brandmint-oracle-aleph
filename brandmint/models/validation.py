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


# ---------------------------------------------------------------------------
# Brand Config Validation
# ---------------------------------------------------------------------------

class ConfigValidationResult(BaseModel):
    """Result of brand config validation."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# Required fields for a valid brand config
REQUIRED_FIELDS = [
    "brand.name",
    "brand.domain_tags",
]

# Recommended fields (generate warnings if missing)
RECOMMENDED_FIELDS = [
    "theme.palette",
    "execution_context.depth_level",
    "execution_context.launch_channel",
    "products",
]

# Valid values for enum-like fields
VALID_DEPTH_LEVELS = ["surface", "focused", "comprehensive", "exhaustive"]
VALID_CHANNELS = ["dtc", "crowdfunding", "enterprise", "app", "saas", "social"]


def _get_nested(data: dict, dot_path: str) -> Any:
    """Get value from nested dict using dot notation."""
    current = data
    for key in dot_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def validate_brand_config(config: dict) -> ConfigValidationResult:
    """Validate a brand configuration dictionary.
    
    Checks for:
    - Required fields presence
    - Recommended fields (warnings)
    - Valid enum values
    - Palette hex format
    
    Args:
        config: Brand configuration dict (from yaml.safe_load)
        
    Returns:
        ConfigValidationResult with errors and warnings
        
    Example:
        result = validate_brand_config(config)
        if not result.valid:
            for error in result.errors:
                print(f"Error: {error}")
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # Check required fields
    for field_path in REQUIRED_FIELDS:
        value = _get_nested(config, field_path)
        if value is None:
            errors.append(f"Missing required field: {field_path}")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Empty required field: {field_path}")
        elif isinstance(value, list) and len(value) == 0:
            errors.append(f"Empty required list: {field_path}")
    
    # Check recommended fields
    for field_path in RECOMMENDED_FIELDS:
        value = _get_nested(config, field_path)
        if value is None:
            warnings.append(f"Missing recommended field: {field_path}")
    
    # Validate depth level if present
    depth = _get_nested(config, "execution_context.depth_level")
    if depth is not None and depth not in VALID_DEPTH_LEVELS:
        errors.append(
            f"Invalid depth_level '{depth}'. "
            f"Must be one of: {', '.join(VALID_DEPTH_LEVELS)}"
        )
    
    # Validate launch channel if present
    channel = _get_nested(config, "execution_context.launch_channel")
    if channel is not None and channel not in VALID_CHANNELS:
        warnings.append(
            f"Uncommon launch_channel '{channel}'. "
            f"Typical values: {', '.join(VALID_CHANNELS)}"
        )
    
    # Validate palette hex codes
    palette = _get_nested(config, "theme.palette")
    if palette and isinstance(palette, dict):
        for name, value in palette.items():
            if isinstance(value, str):
                if not value.startswith("#"):
                    errors.append(f"Palette color '{name}' must start with #")
                elif len(value) not in [4, 7]:  # #RGB or #RRGGBB
                    errors.append(
                        f"Palette color '{name}' has invalid format: {value}"
                    )
    
    # Validate products if present
    products = _get_nested(config, "products")
    if products and isinstance(products, list):
        for i, product in enumerate(products):
            if not isinstance(product, dict):
                errors.append(f"Product {i} must be a dictionary")
            elif "name" not in product:
                warnings.append(f"Product {i} missing 'name' field")
    
    return ConfigValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_config_file(config_path: str) -> ConfigValidationResult:
    """Load and validate a brand config YAML file.
    
    Args:
        config_path: Path to brand-config.yaml
        
    Returns:
        ConfigValidationResult
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    import yaml
    from pathlib import Path
    
    path = Path(config_path)
    if not path.exists():
        return ConfigValidationResult(
            valid=False,
            errors=[f"Config file not found: {config_path}"]
        )
    
    try:
        with open(path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return ConfigValidationResult(
            valid=False,
            errors=[f"YAML parsing error: {e}"]
        )
    
    if not isinstance(config, dict):
        return ConfigValidationResult(
            valid=False,
            errors=["Config file must contain a YAML dictionary"]
        )
    
    return validate_brand_config(config)
