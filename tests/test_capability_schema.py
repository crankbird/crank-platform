"""
Tests for capability schema definitions.

Validates that:
- Capability definitions are well-formed
- Version compatibility works correctly
- JSON schemas are valid
- Error codes are properly structured
"""

import pytest
from pydantic import ValidationError

from crank.capabilities.schema import (
    CSR_SIGNING,
    DOCUMENT_CONVERSION,
    EMAIL_CLASSIFICATION,
    EMAIL_PARSING,
    IMAGE_CLASSIFICATION,
    STREAMING_CLASSIFICATION,
    CapabilityDefinition,
    CapabilityVersion,
    ErrorCode,
    IOContract,
)


class TestCapabilityVersion:
    """Test semantic versioning for capabilities."""

    def test_version_creation(self) -> None:
        """Test creating a version."""
        v = CapabilityVersion(major=1, minor=2, patch=3)
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert str(v) == "1.2.3"

    def test_version_parse(self) -> None:
        """Test parsing version strings."""
        v = CapabilityVersion.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_version_parse_invalid(self) -> None:
        """Test parsing invalid version strings."""
        with pytest.raises(ValueError):
            CapabilityVersion.parse("1.2")
        with pytest.raises(ValueError):
            CapabilityVersion.parse("not.a.version")
        with pytest.raises(ValueError):
            CapabilityVersion.parse("1.2.3.4")

    def test_version_compatibility_same_major(self) -> None:
        """Test that same major versions are compatible."""
        v1 = CapabilityVersion(major=1, minor=0, patch=0)
        v2 = CapabilityVersion(major=1, minor=5, patch=2)
        assert v1.is_compatible_with(v2)
        assert v2.is_compatible_with(v1)

    def test_version_compatibility_different_major(self) -> None:
        """Test that different major versions are incompatible."""
        v1 = CapabilityVersion(major=1, minor=0, patch=0)
        v2 = CapabilityVersion(major=2, minor=0, patch=0)
        assert not v1.is_compatible_with(v2)
        assert not v2.is_compatible_with(v1)

    def test_version_negative_numbers(self) -> None:
        """Test that negative version numbers are rejected."""
        with pytest.raises(ValidationError):
            CapabilityVersion(major=-1, minor=0, patch=0)
        with pytest.raises(ValidationError):
            CapabilityVersion(major=1, minor=-1, patch=0)
        with pytest.raises(ValidationError):
            CapabilityVersion(major=1, minor=0, patch=-1)


class TestErrorCode:
    """Test error code definitions."""

    def test_error_code_creation(self) -> None:
        """Test creating an error code."""
        ec = ErrorCode(
            code="TEST_ERROR",
            description="This is a test error",
            retryable=True,
        )
        assert ec.code == "TEST_ERROR"
        assert ec.description == "This is a test error"
        assert ec.retryable is True
        assert str(ec) == "TEST_ERROR"

    def test_error_code_default_retryable(self) -> None:
        """Test that retryable defaults to False."""
        ec = ErrorCode(code="ERROR", description="Error")
        assert ec.retryable is False


class TestIOContract:
    """Test input/output contracts."""

    def test_io_contract_creation(self) -> None:
        """Test creating an IO contract."""
        contract = IOContract(
            input_schema={
                "type": "object",
                "properties": {"value": {"type": "string"}},
            },
            output_schema={
                "type": "object",
                "properties": {"result": {"type": "string"}},
            },
            error_codes=[
                ErrorCode(code="ERR1", description="Error 1"),
            ],
        )
        assert contract.input_schema["type"] == "object"
        assert contract.output_schema["type"] == "object"
        assert len(contract.error_codes) == 1

    def test_io_contract_schema_validation(self) -> None:
        """Test that schemas must have 'type' field."""
        with pytest.raises(ValidationError, match="Schema must have a 'type' field"):
            IOContract(
                input_schema={"properties": {}},  # Missing 'type'
                output_schema={"type": "object"},
            )

    def test_io_contract_empty_error_codes(self) -> None:
        """Test that error_codes defaults to empty list."""
        contract = IOContract(
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
        assert contract.error_codes == []


class TestCapabilityDefinition:
    """Test capability definitions."""

    def test_capability_creation(self) -> None:
        """Test creating a capability."""
        cap = CapabilityDefinition(
            id="test.capability",
            version=CapabilityVersion(major=1, minor=0, patch=0),
            name="Test Capability",
            description="A test capability",
            contract=IOContract(
                input_schema={"type": "object"},
                output_schema={"type": "object"},
            ),
        )
        assert cap.id == "test.capability"
        assert cap.version.major == 1
        assert cap.name == "Test Capability"
        assert str(cap) == "test.capability@1.0.0"

    def test_capability_with_metadata(self) -> None:
        """Test capability with optional metadata."""
        cap = CapabilityDefinition(
            id="test.capability",
            version=CapabilityVersion(major=1, minor=0, patch=0),
            name="Test Capability",
            description="A test capability",
            contract=IOContract(
                input_schema={"type": "object"},
                output_schema={"type": "object"},
            ),
            tags=["test", "example"],
            requires_gpu=True,
            estimated_duration_ms=500,
        )
        assert cap.tags == ["test", "example"]
        assert cap.requires_gpu is True
        assert cap.estimated_duration_ms == 500

    def test_capability_version_compatibility(self) -> None:
        """Test capability version compatibility check."""
        cap = CapabilityDefinition(
            id="test.capability",
            version=CapabilityVersion(major=1, minor=5, patch=0),
            name="Test",
            description="Test",
            contract=IOContract(
                input_schema={"type": "object"},
                output_schema={"type": "object"},
            ),
        )

        # Same major version = compatible
        assert cap.is_compatible_with(CapabilityVersion(major=1, minor=0, patch=0))

        # Different major version = incompatible
        assert not cap.is_compatible_with(CapabilityVersion(major=2, minor=0, patch=0))


class TestStandardCapabilities:
    """Test the standard capability catalog."""

    def test_document_conversion_capability(self) -> None:
        """Test DOCUMENT_CONVERSION capability is well-formed."""
        assert DOCUMENT_CONVERSION.id == "document.convert"
        assert DOCUMENT_CONVERSION.version.major == 1
        assert "document" in DOCUMENT_CONVERSION.tags
        assert len(DOCUMENT_CONVERSION.contract.error_codes) == 3

        # Verify input schema
        input_props = DOCUMENT_CONVERSION.contract.input_schema["properties"]
        assert "document_data" in input_props
        assert "source_format" in input_props
        assert "target_format" in input_props

        # Verify output schema
        output_props = DOCUMENT_CONVERSION.contract.output_schema["properties"]
        assert "converted_data" in output_props

    def test_email_classification_capability(self) -> None:
        """Test EMAIL_CLASSIFICATION capability is well-formed."""
        assert EMAIL_CLASSIFICATION.id == "email.classify"
        assert EMAIL_CLASSIFICATION.version.major == 1
        assert "ml" in EMAIL_CLASSIFICATION.tags
        assert "nlp" in EMAIL_CLASSIFICATION.tags

        # Verify it has error codes
        assert len(EMAIL_CLASSIFICATION.contract.error_codes) >= 1

        # Verify input accepts classification types
        input_props = EMAIL_CLASSIFICATION.contract.input_schema["properties"]
        assert "classification_types" in input_props

    def test_email_parsing_capability(self) -> None:
        """Test EMAIL_PARSING capability is well-formed."""
        assert EMAIL_PARSING.id == "email.parse"
        assert "parsing" in EMAIL_PARSING.tags

        # Should be fast (< 100ms typically)
        assert EMAIL_PARSING.estimated_duration_ms is not None
        assert EMAIL_PARSING.estimated_duration_ms < 100

    def test_image_classification_capability(self) -> None:
        """Test IMAGE_CLASSIFICATION capability is well-formed."""
        assert IMAGE_CLASSIFICATION.id == "image.classify"
        assert "cv" in IMAGE_CLASSIFICATION.tags

        # Should not require GPU (can run on CPU)
        assert IMAGE_CLASSIFICATION.requires_gpu is False

        # Verify input schema
        input_props = IMAGE_CLASSIFICATION.contract.input_schema["properties"]
        assert "image_data" in input_props
        assert "classification_types" in input_props

    def test_streaming_classification_capability(self) -> None:
        """Test STREAMING_CLASSIFICATION capability is well-formed."""
        assert STREAMING_CLASSIFICATION.id == "streaming.email.classify"
        assert "streaming" in STREAMING_CLASSIFICATION.tags

        # Streaming should be relatively fast
        assert STREAMING_CLASSIFICATION.estimated_duration_ms is not None
        assert STREAMING_CLASSIFICATION.estimated_duration_ms < 200

    def test_csr_signing_capability(self) -> None:
        """Test CSR_SIGNING capability is well-formed."""
        assert CSR_SIGNING.id == "certificate.sign_csr"
        assert "pki" in CSR_SIGNING.tags
        assert "security" in CSR_SIGNING.tags

        # Verify input schema
        input_props = CSR_SIGNING.contract.input_schema["properties"]
        assert "csr_pem" in input_props
        assert "certificate_type" in input_props

        # Verify output schema
        output_props = CSR_SIGNING.contract.output_schema["properties"]
        assert "certificate_pem" in output_props
        assert "serial_number" in output_props

    def test_all_capabilities_have_error_codes(self) -> None:
        """Test that all standard capabilities define error codes."""
        capabilities = [
            DOCUMENT_CONVERSION,
            EMAIL_CLASSIFICATION,
            EMAIL_PARSING,
            IMAGE_CLASSIFICATION,
            STREAMING_CLASSIFICATION,
            CSR_SIGNING,
        ]

        for cap in capabilities:
            assert len(cap.contract.error_codes) > 0, f"{cap.id} has no error codes"

    def test_all_capabilities_have_tags(self) -> None:
        """Test that all standard capabilities have tags."""
        capabilities = [
            DOCUMENT_CONVERSION,
            EMAIL_CLASSIFICATION,
            EMAIL_PARSING,
            IMAGE_CLASSIFICATION,
            STREAMING_CLASSIFICATION,
            CSR_SIGNING,
        ]

        for cap in capabilities:
            assert len(cap.tags) > 0, f"{cap.id} has no tags"

    def test_all_capabilities_have_unique_ids(self) -> None:
        """Test that all standard capabilities have unique IDs."""
        capabilities = [
            DOCUMENT_CONVERSION,
            EMAIL_CLASSIFICATION,
            EMAIL_PARSING,
            IMAGE_CLASSIFICATION,
            STREAMING_CLASSIFICATION,
            CSR_SIGNING,
        ]

        ids = [cap.id for cap in capabilities]
        assert len(ids) == len(set(ids)), "Duplicate capability IDs found"

    def test_capability_serialization(self) -> None:
        """Test that capabilities can be serialized/deserialized."""
        original = EMAIL_CLASSIFICATION

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = CapabilityDefinition(**data)

        assert restored.id == original.id
        assert restored.version.major == original.version.major
        assert restored.name == original.name
        assert restored.contract.input_schema == original.contract.input_schema
