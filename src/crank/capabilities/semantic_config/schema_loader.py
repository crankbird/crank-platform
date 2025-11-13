"""
Schema loader for philosophical analysis configuration.

This module loads and validates the philosophical schema from JSON configuration
and provides structured access to DNA markers, patterns, and scoring thresholds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeAlias, cast

from pydantic import BaseModel, Field

JSONPrimitive = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | dict[str, "JSONValue"] | list["JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]


def _expect_object(value: JSONValue | None, label: str) -> JSONObject:
    """Ensure the JSON value is an object and narrow the static type."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return cast(JSONObject, value)


def _object_or_empty(source: JSONObject, key: str) -> JSONObject:
    """Fetch an object-valued key, defaulting to an empty object if unset."""
    value = source.get(key)
    if value is None:
        return {}
    return _expect_object(value, key)


def _expect_array(value: JSONValue | None, label: str) -> list[JSONValue]:
    """Ensure the JSON value is an array and narrow the static type."""
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _expect_number(value: JSONValue, label: str) -> float:
    """Ensure the JSON value is numeric and return its float representation."""
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"{label} must be numeric")


class DNAMarker(BaseModel):
    """Individual DNA marker configuration for philosophical analysis."""

    name: str = Field(description="Human-readable name for the marker")
    description: str = Field(description="Detailed description of what this marker detects")
    keywords: list[str] = Field(description="Keywords that indicate this marker")
    patterns: list[str] = Field(description="Regex patterns for detection")
    weight: float = Field(description="Weighting factor for scoring")


class SecondaryTheme(BaseModel):
    """Secondary theme configuration for content categorization."""

    name: str = Field(description="Human-readable name for the theme")
    description: str = Field(description="Description of the theme domain")
    keywords: list[str] = Field(description="Keywords that indicate this theme")
    weight: float = Field(description="Weighting factor for scoring")


class PhilosophicalSchema(BaseModel):
    """Complete philosophical schema for content analysis."""

    core_principle: str = Field(description="The fundamental principle guiding analysis")
    primary_markers: dict[str, DNAMarker] = Field(description="Main philosophical DNA markers")
    secondary_themes: dict[str, SecondaryTheme] = Field(description="Supporting themes and categories")
    coherence_levels: dict[str, str] = Field(description="Coherence scoring explanations")
    readiness_thresholds: dict[str, float] = Field(description="Thresholds for various actions")
    persona_mappings: dict[str, list[str]] = Field(description="Persona associations for each marker")

    @property
    def dna_markers(self) -> list[DNAMarker]:
        """Get list of all DNA marker objects."""
        return list(self.primary_markers.values())

    @property
    def marker_codes(self) -> list[str]:
        """Get list of all primary marker codes (SHM, TUD, etc.)."""
        return list(self.primary_markers.keys())

    @property
    def theme_codes(self) -> list[str]:
        """Get list of all secondary theme codes (BIZ, TECH, etc.)."""
        return list(self.secondary_themes.keys())

    def get_marker(self, marker_id: str) -> DNAMarker | None:
        """Get a specific DNA marker by code."""
        return self.primary_markers.get(marker_id)

    def get_theme(self, theme_id: str) -> SecondaryTheme | None:
        """Get a specific theme by code."""
        return self.secondary_themes.get(theme_id)

    def get_readiness_threshold(self, action_name: str) -> float | None:
        """Get the threshold for a specific readiness action."""
        return self.readiness_thresholds.get(action_name)


def load_schema(schema_path: Path | None = None) -> PhilosophicalSchema:
    """
    Load the philosophical schema from JSON configuration.

    Args:
        schema_path: Optional path to schema file. If None, uses default location.

    Returns:
        PhilosophicalSchema instance with loaded configuration.

    Raises:
        FileNotFoundError: If schema file cannot be found
        ValueError: If schema file is invalid
    """
    if schema_path is None:
        # Default to the schema in this package
        schema_path = Path(__file__).parent / "philosophical-schema.json"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(schema_path, encoding="utf-8") as f:
            raw_payload = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file: {e}") from e

    if not isinstance(raw_payload, dict):
        raise ValueError("Schema root must be a JSON object")

    raw_data: JSONObject = cast(JSONObject, raw_payload)

    # Transform the raw data structure to match our Pydantic models
    try:
        primary_marker_source = _object_or_empty(raw_data, "primary_markers")
        primary_markers: dict[str, DNAMarker] = {}
        for marker_id, marker_data in primary_marker_source.items():
            marker_fields = _expect_object(marker_data, "Marker definitions")
            primary_markers[marker_id] = DNAMarker.model_validate(marker_fields)

        secondary_theme_source = _object_or_empty(raw_data, "secondary_themes")
        secondary_themes: dict[str, SecondaryTheme] = {}
        for theme_id, theme_data in secondary_theme_source.items():
            theme_fields = _expect_object(theme_data, "Theme definitions")
            secondary_themes[theme_id] = SecondaryTheme.model_validate(theme_fields)

        coherence_source = _object_or_empty(raw_data, "coherence_levels")
        coherence_levels: dict[str, str] = {
            str(level): str(description) for level, description in coherence_source.items()
        }

        readiness_source = _object_or_empty(raw_data, "readiness_thresholds")
        readiness_thresholds: dict[str, float] = {}
        for action_name, raw_threshold in readiness_source.items():
            readiness_thresholds[action_name] = _expect_number(
                raw_threshold, "readiness threshold value"
            )

        persona_source = _object_or_empty(raw_data, "persona_mappings")
        persona_mappings: dict[str, list[str]] = {}
        for persona_id, persona_list in persona_source.items():
            persona_entries = _expect_array(persona_list, "Persona mapping values")
            persona_mappings[persona_id] = [str(persona) for persona in persona_entries]

        return PhilosophicalSchema(
            core_principle=str(raw_data.get("core_principle", "")),
            primary_markers=primary_markers,
            secondary_themes=secondary_themes,
            coherence_levels=coherence_levels,
            readiness_thresholds=readiness_thresholds,
            persona_mappings=persona_mappings,
        )

    except Exception as e:
        raise ValueError(f"Failed to parse schema structure: {e}") from e


# Global instance for easy access
_schema_instance: PhilosophicalSchema | None = None


def get_schema() -> PhilosophicalSchema:
    """Get the global schema instance, loading it if necessary."""
    global _schema_instance
    if _schema_instance is None:
        _schema_instance = load_schema()
    return _schema_instance
