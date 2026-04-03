"""
State file validation and recovery.

Provides JSON schema validation and auto-repair for pipeline state files.
Prevents crashes from corrupted or malformed state data.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON Schemas
# ---------------------------------------------------------------------------

EXECUTION_STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario": {"type": ["string", "null"]},
        "wave_states": {
            "type": "object",
            "patternProperties": {
                "^[0-9]+$": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "failed", "skipped"]
                        },
                        "started_at": {"type": ["string", "null"]},
                        "completed_at": {"type": ["string", "null"]},
                        "skill_outputs": {"type": "object"},
                    },
                    "required": ["status"],
                }
            }
        },
        "completed_skills": {"type": "array", "items": {"type": "string"}},
        "failed_skills": {"type": "array", "items": {"type": "string"}},
        "last_checkpoint": {"type": ["string", "null"]},
    },
    "required": ["wave_states"],
}

NOTEBOOKLM_STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "notebook_id": {"type": ["string", "null"]},
        "notebook_fingerprint": {"type": ["string", "null"]},
        "notebook_url": {"type": ["string", "null"]},
        "sources_uploaded": {"type": "array", "items": {"type": "string"}},
        "artifacts_generated": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string"},
                        "artifact_id": {"type": ["string", "null"]},
                        "local_path": {"type": ["string", "null"]},
                        "submitted_at": {"type": ["string", "null"]},
                        "completed_at": {"type": ["string", "null"]},
                    }
                }
            }
        },
        "last_updated": {"type": ["string", "null"]},
    },
}


def validate_schema(data: dict, schema: dict) -> Tuple[bool, Optional[str]]:
    """Validate data against JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema definition
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Simple recursive validation (lightweight alternative to jsonschema)
        def check_type(value: Any, expected_type: Any) -> bool:
            if isinstance(expected_type, list):
                return any(check_type(value, t) for t in expected_type)
            
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict,
                "null": type(None),
            }
            
            if expected_type == "null":
                return value is None
            
            return isinstance(value, type_map.get(expected_type, type(None)))
        
        def validate_object(obj: dict, obj_schema: dict) -> Tuple[bool, Optional[str]]:
            # Check type
            if obj_schema.get("type") == "object" and not isinstance(obj, dict):
                return False, f"Expected object, got {type(obj).__name__}"
            
            # Check required fields
            required = obj_schema.get("required", [])
            missing = [f for f in required if f not in obj]
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"
            
            # Check properties
            properties = obj_schema.get("properties", {})
            for key, value in obj.items():
                if key in properties:
                    prop_schema = properties[key]
                    
                    # Check type
                    if "type" in prop_schema:
                        if not check_type(value, prop_schema["type"]):
                            return False, f"Field '{key}': expected {prop_schema['type']}, got {type(value).__name__}"
                    
                    # Check enum
                    if "enum" in prop_schema and value not in prop_schema["enum"]:
                        return False, f"Field '{key}': value '{value}' not in {prop_schema['enum']}"
                    
                    # Recurse for nested objects
                    if isinstance(value, dict) and prop_schema.get("type") == "object":
                        valid, error = validate_object(value, prop_schema)
                        if not valid:
                            return False, f"Field '{key}': {error}"
            
            # Check pattern properties
            pattern_props = obj_schema.get("patternProperties", {})
            for pattern, pattern_schema in pattern_props.items():
                for key, value in obj.items():
                    import re
                    if re.match(pattern, key):
                        if isinstance(value, dict):
                            valid, error = validate_object(value, pattern_schema)
                            if not valid:
                                return False, f"Field '{key}': {error}"
            
            return True, None
        
        return validate_object(data, schema)
        
    except Exception as e:
        return False, f"Validation error: {e}"


# ---------------------------------------------------------------------------
# State validators
# ---------------------------------------------------------------------------

class StateValidator:
    """Validates and repairs pipeline state files."""
    
    @staticmethod
    def validate_execution_state(state: dict) -> Tuple[bool, Optional[str], dict]:
        """Validate execution state file.
        
        Args:
            state: State dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message, repaired_state)
            If is_valid is False, repaired_state contains auto-repaired version
        """
        valid, error = validate_schema(state, EXECUTION_STATE_SCHEMA)
        
        if valid:
            return True, None, state
        
        # Auto-repair: create minimal valid state
        logger.warning(f"Invalid execution state: {error}. Attempting repair...")
        
        repaired = {
            "scenario": state.get("scenario"),
            "wave_states": {},
            "completed_skills": [],
            "failed_skills": [],
            "last_checkpoint": None,
        }
        
        # Try to preserve wave states
        if isinstance(state.get("wave_states"), dict):
            for wave_num, wave_state in state["wave_states"].items():
                if isinstance(wave_state, dict):
                    repaired["wave_states"][str(wave_num)] = {
                        "status": wave_state.get("status", "pending"),
                        "started_at": wave_state.get("started_at"),
                        "completed_at": wave_state.get("completed_at"),
                        "skill_outputs": wave_state.get("skill_outputs", {}),
                    }
        
        # Preserve skill lists
        if isinstance(state.get("completed_skills"), list):
            repaired["completed_skills"] = [
                s for s in state["completed_skills"] if isinstance(s, str)
            ]
        if isinstance(state.get("failed_skills"), list):
            repaired["failed_skills"] = [
                s for s in state["failed_skills"] if isinstance(s, str)
            ]
        
        logger.info("State repaired successfully")
        return False, error, repaired
    
    @staticmethod
    def validate_notebooklm_state(state: dict) -> Tuple[bool, Optional[str], dict]:
        """Validate NotebookLM state file.
        
        Args:
            state: State dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message, repaired_state)
        """
        valid, error = validate_schema(state, NOTEBOOKLM_STATE_SCHEMA)
        
        if valid:
            return True, None, state
        
        # Auto-repair
        logger.warning(f"Invalid NotebookLM state: {error}. Attempting repair...")
        
        repaired = {
            "notebook_id": state.get("notebook_id"),
            "notebook_fingerprint": state.get("notebook_fingerprint"),
            "notebook_url": state.get("notebook_url"),
            "sources_uploaded": [],
            "artifacts_generated": {},
            "last_updated": datetime.now().isoformat(),
        }
        
        # Preserve uploaded sources
        if isinstance(state.get("sources_uploaded"), list):
            repaired["sources_uploaded"] = [
                s for s in state["sources_uploaded"] if isinstance(s, str)
            ]
        
        # Preserve artifacts
        if isinstance(state.get("artifacts_generated"), dict):
            for artifact_id, artifact_data in state["artifacts_generated"].items():
                if isinstance(artifact_data, dict):
                    repaired["artifacts_generated"][artifact_id] = {
                        "id": artifact_data.get("id", artifact_id),
                        "status": artifact_data.get("status", "unknown"),
                        "artifact_id": artifact_data.get("artifact_id"),
                        "local_path": artifact_data.get("local_path"),
                        "submitted_at": artifact_data.get("submitted_at"),
                        "completed_at": artifact_data.get("completed_at"),
                    }
        
        logger.info("NotebookLM state repaired successfully")
        return False, error, repaired


# ---------------------------------------------------------------------------
# Safe load/save functions
# ---------------------------------------------------------------------------

def load_state_safe(
    path: Path,
    state_type: str = "execution",
) -> Tuple[dict, bool]:
    """Safely load state file with validation and auto-repair.
    
    Args:
        path: Path to state file
        state_type: Type of state ("execution" or "notebooklm")
    
    Returns:
        Tuple of (state_dict, was_repaired)
        Returns empty valid state if file doesn't exist
    """
    if not path.exists():
        logger.debug(f"State file not found: {path}")
        if state_type == "execution":
            return {"wave_states": {}, "completed_skills": [], "failed_skills": []}, False
        else:
            return {"sources_uploaded": [], "artifacts_generated": {}}, False
    
    # Try to load JSON
    try:
        with path.open("r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load state file {path}: {e}")
        # Return empty state
        if state_type == "execution":
            return {"wave_states": {}, "completed_skills": [], "failed_skills": []}, False
        else:
            return {"sources_uploaded": [], "artifacts_generated": {}}, False
    
    # Validate
    validator = StateValidator()
    if state_type == "execution":
        valid, error, repaired = validator.validate_execution_state(state)
    else:
        valid, error, repaired = validator.validate_notebooklm_state(state)
    
    if valid:
        return state, False
    
    # Save backup of corrupted state
    backup_path = path.parent / f"{path.stem}.corrupted-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    try:
        with backup_path.open("w") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Backed up corrupted state to: {backup_path}")
    except OSError:
        pass
    
    # Save repaired state
    try:
        with path.open("w") as f:
            json.dump(repaired, f, indent=2)
        logger.info(f"Saved repaired state to: {path}")
    except OSError as e:
        logger.error(f"Failed to save repaired state: {e}")
    
    return repaired, True


def save_state_safe(
    state: dict,
    path: Path,
    state_type: str = "execution",
) -> bool:
    """Safely save state file with pre-save validation.
    
    Args:
        state: State dictionary to save
        path: Path to save to
        state_type: Type of state ("execution" or "notebooklm")
    
    Returns:
        True if saved successfully, False otherwise
    """
    # Validate before saving
    validator = StateValidator()
    if state_type == "execution":
        valid, error, _ = validator.validate_execution_state(state)
    else:
        valid, error, _ = validator.validate_notebooklm_state(state)
    
    if not valid:
        logger.error(f"Refusing to save invalid state: {error}")
        return False
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    try:
        with path.open("w") as f:
            json.dump(state, f, indent=2)
        return True
    except OSError as e:
        logger.error(f"Failed to save state to {path}: {e}")
        return False
