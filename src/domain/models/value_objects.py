"""
Value Objects for the requirements domain.
Value objects are immutable objects that represent concepts in the domain.
"""

from dataclasses import dataclass
from typing import Union, Optional
import uuid
from enum import Enum


class PriorityLevel(Enum):
    """Priority levels for requirements."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NICE_TO_HAVE = "nice_to_have"


class ComplexityScale(Enum):
    """Complexity scales for requirements."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass(frozen=True)
class Priority:
    """Value object representing requirement priority."""

    level: PriorityLevel
    reason: Optional[str] = None

    def __post_init__(self):
        """Validate priority."""
        if not isinstance(self.level, PriorityLevel):
            raise ValueError("Priority level must be a PriorityLevel enum")

    @property
    def numeric_value(self) -> int:
        """Get numeric representation of priority (higher = more important)."""
        priority_values = {
            PriorityLevel.CRITICAL: 5,
            PriorityLevel.HIGH: 4,
            PriorityLevel.MEDIUM: 3,
            PriorityLevel.LOW: 2,
            PriorityLevel.NICE_TO_HAVE: 1
        }
        return priority_values[self.level]

    def is_higher_than(self, other: 'Priority') -> bool:
        """Check if this priority is higher than another."""
        return self.numeric_value > other.numeric_value

    def __str__(self) -> str:
        return f"Priority({self.level.value})"


@dataclass(frozen=True)
class ComplexityLevel:
    """Value object representing requirement complexity."""

    scale: ComplexityScale
    explanation: Optional[str] = None

    def __post_init__(self):
        """Validate complexity level."""
        if not isinstance(self.scale, ComplexityScale):
            raise ValueError("Complexity scale must be a ComplexityScale enum")

    @property
    def numeric_value(self) -> int:
        """Get numeric representation of complexity (higher = more complex)."""
        complexity_values = {
            ComplexityScale.TRIVIAL: 1,
            ComplexityScale.SIMPLE: 2,
            ComplexityScale.MODERATE: 3,
            ComplexityScale.COMPLEX: 4,
            ComplexityScale.VERY_COMPLEX: 5
        }
        return complexity_values[self.scale]

    def is_more_complex_than(self, other: 'ComplexityLevel') -> bool:
        """Check if this complexity is higher than another."""
        return self.numeric_value > other.numeric_value

    def __str__(self) -> str:
        return f"Complexity({self.scale.value})"


@dataclass(frozen=True)
class BusinessValue:
    """Value object representing business value of a requirement."""

    score: int
    justification: Optional[str] = None

    def __post_init__(self):
        """Validate business value."""
        if not isinstance(self.score, int):
            raise ValueError("Business value score must be an integer")

        if self.score < 0 or self.score > 100:
            raise ValueError("Business value score must be between 0 and 100")

    @property
    def is_high_value(self) -> bool:
        """Check if this represents high business value (>= 70)."""
        return self.score >= 70

    @property
    def is_medium_value(self) -> bool:
        """Check if this represents medium business value (30-69)."""
        return 30 <= self.score < 70

    @property
    def is_low_value(self) -> bool:
        """Check if this represents low business value (< 30)."""
        return self.score < 30

    def __str__(self) -> str:
        return f"BusinessValue({self.score})"


@dataclass(frozen=True)
class StoryPoints:
    """Value object representing story points estimation."""

    points: Union[int, float]
    estimation_method: Optional[str] = None

    def __post_init__(self):
        """Validate story points."""
        if not isinstance(self.points, (int, float)):
            raise ValueError("Story points must be a number")

        if self.points < 0:
            raise ValueError("Story points cannot be negative")

        # Common Fibonacci sequence values for story points
        valid_points = {0, 0.5, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89}
        if self.points not in valid_points:
            # Allow other values but log a warning concept
            pass

    @property
    def is_large_story(self) -> bool:
        """Check if this represents a large story (>= 13 points)."""
        return self.points >= 13

    @property
    def is_epic(self) -> bool:
        """Check if this represents an epic (>= 21 points)."""
        return self.points >= 21

    def __str__(self) -> str:
        return f"StoryPoints({self.points})"


@dataclass(frozen=True)
class RequirementIdentifier:
    """Value object for requirement identifiers."""

    prefix: str
    number: int
    version: Optional[str] = None

    def __post_init__(self):
        """Validate requirement identifier."""
        if not self.prefix or not self.prefix.strip():
            raise ValueError("Requirement prefix cannot be empty")

        if not isinstance(self.number, int) or self.number <= 0:
            raise ValueError("Requirement number must be a positive integer")

        if self.version and not self.version.strip():
            raise ValueError("Version cannot be empty if provided")

    @property
    def full_identifier(self) -> str:
        """Get the full identifier string."""
        if self.version:
            return f"{self.prefix}-{self.number:04d}.{self.version}"
        return f"{self.prefix}-{self.number:04d}"

    @classmethod
    def from_string(cls, identifier: str) -> 'RequirementIdentifier':
        """Create a RequirementIdentifier from a string."""
        if not identifier or not identifier.strip():
            raise ValueError("Identifier string cannot be empty")

        parts = identifier.split('-')
        if len(parts) != 2:
            raise ValueError("Identifier must be in format PREFIX-NUMBER[.VERSION]")

        prefix = parts[0]
        number_version = parts[1]

        if '.' in number_version:
            number_str, version = number_version.split('.', 1)
        else:
            number_str = number_version
            version = None

        try:
            number = int(number_str)
        except ValueError:
            raise ValueError("Number part must be an integer")

        return cls(prefix=prefix, number=number, version=version)

    def increment(self) -> 'RequirementIdentifier':
        """Create a new identifier with incremented number."""
        return RequirementIdentifier(
            prefix=self.prefix,
            number=self.number + 1,
            version=self.version
        )

    def with_version(self, version: str) -> 'RequirementIdentifier':
        """Create a new identifier with a different version."""
        return RequirementIdentifier(
            prefix=self.prefix,
            number=self.number,
            version=version
        )

    def __str__(self) -> str:
        return self.full_identifier

    def __lt__(self, other: 'RequirementIdentifier') -> bool:
        """Compare identifiers for sorting."""
        if self.prefix != other.prefix:
            return self.prefix < other.prefix
        return self.number < other.number