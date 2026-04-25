"""Validator Types and Identity - Feature 071.

Defines validator types for acceptance validation.
Validator runs in isolated context from executor.

Integration with:
- Feature 069 (AcceptancePack/AcceptanceResult)
- Feature 071 (AcceptanceRunner)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ValidatorType(str, Enum):
    """Types of validators for acceptance (Feature 069/071)."""
    
    AI_SESSION = "ai_session"
    HUMAN_REVIEW = "human_review"
    AUTOMATED_SCRIPT = "automated_script"


class ValidatorContext(str, Enum):
    """Execution context for validator."""
    
    INDEPENDENT = "independent"
    DEFAULT = "default"


@dataclass
class ValidatorIdentity:
    """Identity and context of validator (Feature 071)."""
    
    validator_type: ValidatorType
    validator_id: str
    validator_context: ValidatorContext = ValidatorContext.INDEPENDENT
    invoked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_type": self.validator_type.value,
            "validator_id": self.validator_id,
            "validator_context": self.validator_context.value,
            "invoked_at": self.invoked_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidatorIdentity":
        return cls(
            validator_type=ValidatorType(data.get("validator_type", "ai_session")),
            validator_id=data.get("validator_id", ""),
            validator_context=ValidatorContext(data.get("validator_context", "independent")),
            invoked_at=data.get("invoked_at", datetime.now().isoformat()),
        )


def create_ai_validator_identity(session_id: str) -> ValidatorIdentity:
    """Create validator identity for AI session."""
    return ValidatorIdentity(
        validator_type=ValidatorType.AI_SESSION,
        validator_id=session_id,
        validator_context=ValidatorContext.INDEPENDENT,
    )


def create_human_validator_identity(person_id: str) -> ValidatorIdentity:
    """Create validator identity for human reviewer."""
    return ValidatorIdentity(
        validator_type=ValidatorType.HUMAN_REVIEW,
        validator_id=person_id,
        validator_context=ValidatorContext.INDEPENDENT,
    )


def create_script_validator_identity(script_name: str) -> ValidatorIdentity:
    """Create validator identity for automated script."""
    return ValidatorIdentity(
        validator_type=ValidatorType.AUTOMATED_SCRIPT,
        validator_id=script_name,
        validator_context=ValidatorContext.INDEPENDENT,
    )