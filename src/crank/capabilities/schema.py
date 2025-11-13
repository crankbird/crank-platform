"""
Capability Schema Definitions

This module defines the core types for capability declarations and validation.
Workers use these types to declare what they can do, and controllers use them
to validate compatibility and route work appropriately.

Design Philosophy:
- Capabilities are immutable contracts
- Versioning follows semantic versioning (MAJOR.MINOR.PATCH)
- Input/output schemas are JSON Schema compatible
- Error codes are enumerated and documented
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from .semantic_config import PhilosophicalSchema, load_schema


class CapabilityVersion(BaseModel):
    """
    Semantic version for capability definitions.

    Breaking changes require MAJOR bump.
    Backward-compatible additions require MINOR bump.
    Bug fixes require PATCH bump.
    """

    major: int = Field(ge=0, description="Breaking changes")
    minor: int = Field(ge=0, description="Backward-compatible additions")
    patch: int = Field(ge=0, description="Bug fixes")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"CapabilityVersion({self.major}.{self.minor}.{self.patch})"

    def is_compatible_with(self, other: CapabilityVersion) -> bool:
        """Check if this version is compatible with another version."""
        # Same major version = compatible (within reason)
        # Minor/patch differences are acceptable
        return self.major == other.major

    @classmethod
    def parse(cls, version_str: str) -> CapabilityVersion:
        """Parse a version string like '1.2.3' into a CapabilityVersion."""
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version string: {version_str}")
        try:
            major, minor, patch = map(int, parts)
            return cls(major=major, minor=minor, patch=patch)
        except ValueError as e:
            raise ValueError(f"Invalid version string: {version_str}") from e


class ErrorCode(BaseModel):
    """
    Structured error code with description.

    Workers declare what errors they can produce, allowing controllers
    to handle failures appropriately.
    """

    code: str = Field(
        description="Machine-readable error code (e.g., 'INVALID_INPUT')"
    )
    description: str = Field(description="Human-readable error description")
    retryable: bool = Field(
        default=False, description="Whether this error is safe to retry"
    )

    def __str__(self) -> str:
        return self.code


class IOContract(BaseModel):
    """
    Input/output contract for a capability.

    Uses JSON Schema for validation. Defines:
    - What inputs the capability accepts
    - What outputs it produces
    - What errors it can raise
    """

    input_schema: dict[str, Any] = Field(
        description="JSON Schema for input validation"
    )
    output_schema: dict[str, Any] = Field(
        description="JSON Schema for output validation"
    )
    @staticmethod
    def _default_error_codes() -> list[ErrorCode]:
        """Provide a typed default factory for error codes."""
        return []

    error_codes: list[ErrorCode] = Field(
        default_factory=_default_error_codes,
        description="Possible error codes this capability raises",
    )

    @field_validator("input_schema", "output_schema")
    @classmethod
    def validate_json_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure schema is valid JSON Schema."""
        if "type" not in v:
            raise ValueError("Schema must have a 'type' field")
        return v


class CapabilityDefinition(BaseModel):
    """
    Complete capability definition.

    This is the source of truth for what a worker can do. Controllers
    use this to:
    - Validate worker registrations
    - Route work to appropriate workers
    - Check version compatibility
    - Handle errors appropriately
    """

    id: str = Field(
        description="Unique capability identifier (e.g., 'email.classify')"
    )
    version: CapabilityVersion = Field(description="Semantic version")
    name: str = Field(description="Human-readable capability name")
    description: str = Field(description="What this capability does")
    contract: IOContract = Field(description="Input/output contract")

    # Optional metadata
    tags: list[str] = Field(
        default_factory=list, description="Tags for discovery (e.g., 'ml', 'cv', 'nlp')"
    )
    requires_gpu: bool = Field(default=False, description="Whether GPU is required")
    estimated_duration_ms: int | None = Field(
        default=None, description="Typical execution time in milliseconds"
    )

    def __str__(self) -> str:
        return f"{self.id}@{self.version}"

    def __repr__(self) -> str:
        return f"CapabilityDefinition({self.id}@{self.version})"

    def is_compatible_with(self, required_version: CapabilityVersion) -> bool:
        """Check if this capability version satisfies a required version."""
        return self.version.is_compatible_with(required_version)


# =============================================================================
# STANDARD CAPABILITY CATALOG
# =============================================================================
# These are the canonical capability definitions for the Crank Platform.
# Workers MUST use these definitions when declaring capabilities.
# =============================================================================

DOCUMENT_CONVERSION = CapabilityDefinition(
    id="document.convert",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Document Conversion",
    description="Convert documents between formats (PDF, DOCX, TXT, etc.)",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "document_data": {"type": "string", "description": "Base64-encoded document"},
                "source_format": {"type": "string", "enum": ["pdf", "docx", "txt", "html"]},
                "target_format": {"type": "string", "enum": ["pdf", "docx", "txt", "html"]},
            },
            "required": ["document_data", "source_format", "target_format"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "converted_data": {"type": "string", "description": "Base64-encoded converted document"},
                "target_format": {"type": "string"},
                "conversion_time_ms": {"type": "number"},
            },
            "required": ["converted_data", "target_format"],
        },
        error_codes=[
            ErrorCode(code="INVALID_FORMAT", description="Unsupported format", retryable=False),
            ErrorCode(code="CONVERSION_FAILED", description="Conversion process failed", retryable=True),
            ErrorCode(code="CORRUPT_DOCUMENT", description="Document is corrupt or unreadable", retryable=False),
        ],
    ),
    tags=["document", "conversion"],
    estimated_duration_ms=500,
)

EMAIL_CLASSIFICATION = CapabilityDefinition(
    id="email.classify",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Email Classification",
    description="Classify emails by content, sentiment, priority, etc.",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "email_content": {"type": "string", "description": "Email body text"},
                "subject": {"type": "string", "description": "Email subject line"},
                "classification_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["spam", "priority", "sentiment", "category"]},
                },
            },
            "required": ["email_content", "classification_types"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "classifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "value": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        },
                    },
                },
                "processing_time_ms": {"type": "number"},
            },
            "required": ["classifications"],
        },
        error_codes=[
            ErrorCode(code="INVALID_INPUT", description="Email content is invalid", retryable=False),
            ErrorCode(code="CLASSIFIER_UNAVAILABLE", description="ML classifier not loaded", retryable=True),
            ErrorCode(code="CLASSIFICATION_FAILED", description="Classification process failed", retryable=True),
        ],
    ),
    tags=["email", "ml", "nlp"],
    estimated_duration_ms=200,
)

EMAIL_PARSING = CapabilityDefinition(
    id="email.parse",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Email Parsing",
    description="Parse raw email into structured components (headers, body, attachments)",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "raw_email": {"type": "string", "description": "Raw email message (RFC 5322)"},
                "extract_attachments": {"type": "boolean", "default": True},
            },
            "required": ["raw_email"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "headers": {"type": "object"},
                "body": {"type": "string"},
                "attachments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content_type": {"type": "string"},
                            "data": {"type": "string", "description": "Base64-encoded"},
                        },
                    },
                },
                "parsing_time_ms": {"type": "number"},
            },
            "required": ["headers", "body"],
        },
        error_codes=[
            ErrorCode(code="INVALID_EMAIL", description="Malformed email message", retryable=False),
            ErrorCode(code="PARSING_FAILED", description="Email parsing failed", retryable=True),
        ],
    ),
    tags=["email", "parsing"],
    estimated_duration_ms=50,
)

IMAGE_CLASSIFICATION = CapabilityDefinition(
    id="image.classify",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Image Classification",
    description="Classify images using ML models (objects, scenes, NSFW, etc.)",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "image_data": {"type": "string", "description": "Base64-encoded image"},
                "classification_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["objects", "scenes", "nsfw", "faces"]},
                },
                "max_results": {"type": "integer", "default": 5, "minimum": 1},
            },
            "required": ["image_data", "classification_types"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "classifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "label": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        },
                    },
                },
                "processing_time_ms": {"type": "number"},
            },
            "required": ["classifications"],
        },
        error_codes=[
            ErrorCode(code="INVALID_IMAGE", description="Image data is corrupt or invalid", retryable=False),
            ErrorCode(code="MODEL_UNAVAILABLE", description="ML model not loaded", retryable=True),
            ErrorCode(code="CLASSIFICATION_FAILED", description="Classification failed", retryable=True),
        ],
    ),
    tags=["image", "ml", "cv"],
    requires_gpu=False,  # Can run on CPU, GPU optional for speed
    estimated_duration_ms=300,
)

STREAMING_CLASSIFICATION = CapabilityDefinition(
    id="streaming.email.classify",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Streaming Email Classification",
    description="Real-time email classification with streaming results",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "email_content": {"type": "string"},
                "classification_types": {"type": "string"},  # Comma-separated for streaming API
                "stream": {"type": "boolean", "default": True},
            },
            "required": ["email_content", "classification_types"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "value": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                    },
                },
                "processing_time_ms": {"type": "number"},
            },
            "required": ["results"],
        },
        error_codes=[
            ErrorCode(code="INVALID_INPUT", description="Invalid email content", retryable=False),
            ErrorCode(code="STREAM_FAILED", description="Streaming failed", retryable=True),
        ],
    ),
    tags=["email", "ml", "streaming"],
    estimated_duration_ms=150,
)

CSR_SIGNING = CapabilityDefinition(
    id="certificate.sign_csr",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="CSR Signing",
    description="Sign Certificate Signing Requests (CSR) to issue certificates",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "csr_pem": {"type": "string", "description": "PEM-encoded CSR"},
                "validity_days": {"type": "integer", "default": 365, "minimum": 1},
                "certificate_type": {"type": "string", "enum": ["client", "server"]},
            },
            "required": ["csr_pem", "certificate_type"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "certificate_pem": {"type": "string", "description": "PEM-encoded signed certificate"},
                "serial_number": {"type": "string"},
                "not_before": {"type": "string", "format": "date-time"},
                "not_after": {"type": "string", "format": "date-time"},
            },
            "required": ["certificate_pem", "serial_number"],
        },
        error_codes=[
            ErrorCode(code="INVALID_CSR", description="CSR is malformed or invalid", retryable=False),
            ErrorCode(code="SIGNING_FAILED", description="Certificate signing failed", retryable=True),
            ErrorCode(code="CA_UNAVAILABLE", description="CA not available", retryable=True),
        ],
    ),
    tags=["certificate", "security", "pki"],
    estimated_duration_ms=100,
)

_PHILOSOPHICAL_SCHEMA: PhilosophicalSchema = load_schema()


def _build_philosophical_output_schema(schema: PhilosophicalSchema) -> dict[str, Any]:
    """Construct the output schema from the semantic configuration."""
    dna_marker_properties: dict[str, Any] = {
        code: {
            "type": "number",
            "description": f"{marker.name} score (0-1)",
        }
        for code, marker in schema.primary_markers.items()
    }

    secondary_theme_properties: dict[str, Any] = {
        code: {
            "type": "number",
            "description": f"{theme.name} emphasis score (0-1)",
        }
        for code, theme in schema.secondary_themes.items()
    }

    readiness_thresholds: dict[str, Any] = {
        action: {
            "type": "number",
            "description": f"Threshold for {action.replace('_', ' ')} actions",
            "default": threshold,
        }
        for action, threshold in schema.readiness_thresholds.items()
    }

    return {
        "type": "object",
        "properties": {
            "dna_markers": {
                "type": "object",
                "description": "Per-marker confidence scores driven by the semantic schema",
                "properties": dna_marker_properties,
                "required": list(dna_marker_properties.keys()),
                "additionalProperties": False,
            },
            "secondary_themes": {
                "type": "object",
                "description": "Theme alignment scores derived from semantic configuration",
                "properties": secondary_theme_properties,
                "additionalProperties": False,
            },
            "authenticity_score": {
                "type": "number",
                "description": "Authentic vs. performed thinking score (0-1)",
            },
            "analysis_summary": {
                "type": "string",
                "description": "Human-readable analysis summary",
            },
            "confidence": {
                "type": "number",
                "description": "Overall analysis confidence level (0-1)",
            },
            "detected_patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of detected philosophical patterns",
            },
            "readiness_thresholds": {
                "type": "object",
                "description": "Snapshot of readiness thresholds used during analysis",
                "properties": readiness_thresholds,
                "additionalProperties": False,
            },
        },
        "required": ["dna_markers", "authenticity_score", "analysis_summary", "confidence"],
    }


def _build_philosophical_analysis_contract(schema: PhilosophicalSchema) -> IOContract:
    """Create the IO contract using the latest semantic configuration."""
    return IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content to analyze"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["dna_markers", "authenticity", "full_analysis"],
                    "default": "full_analysis",
                },
                "context": {
                    "type": "object",
                    "properties": {
                        "author": {"type": "string", "description": "Optional author context"},
                        "domain": {
                            "type": "string",
                            "description": "Content domain (business, technical, philosophical)",
                        },
                    },
                    "additionalProperties": True,
                },
            },
            "required": ["text"],
        },
        output_schema=_build_philosophical_output_schema(schema),
        error_codes=[
            ErrorCode(
                code="TEXT_TOO_SHORT",
                description="Text too short for meaningful analysis",
                retryable=False,
            ),
            ErrorCode(
                code="ANALYSIS_FAILED",
                description="Philosophical analysis processing failed",
                retryable=True,
            ),
            ErrorCode(
                code="INVALID_CONTEXT",
                description="Invalid context parameters",
                retryable=False,
            ),
        ],
    )


PHILOSOPHICAL_ANALYSIS = CapabilityDefinition(
    id="content.philosophical_analysis",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Philosophical Analysis",
    description="Analyze content for philosophical DNA markers and authentic vs. performed thinking patterns",
    contract=_build_philosophical_analysis_contract(_PHILOSOPHICAL_SCHEMA),
    tags=["content", "analysis", "philosophy", "ml"],
    estimated_duration_ms=500,
)
