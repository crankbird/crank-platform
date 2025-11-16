"""
Capability Contract Testing
============================

Tests that workers meet their declared capability contracts.

Each worker has a manifest in tests/capabilities/manifests/{worker_id}.yaml
that declares:
- Required capabilities (worker MUST provide these)
- Minimum capability count
- Contract requirements (schema, versioning, etc.)

This prevents:
- Accidental capability removal (breaking changes)
- Missing schema/version information
- Silent capability additions without review

When a test fails:
- Worker removed capability → Update worker code or manifest
- Worker added capability → Update manifest (explicit approval)
- Contract violation → Fix worker implementation
"""

from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging import version

# Import all workers for testing
from services.crank_codex_zettel_repository import CodexZettelRepositoryWorker
from services.crank_doc_converter import DocumentConverterWorker
from services.crank_email_classifier import EmailClassifierWorker
from services.crank_email_parser import EmailParserWorker
from services.crank_hello_world import HelloWorldWorker
from services.crank_philosophical_analyzer import PhilosophicalAnalyzerWorker
from services.crank_sonnet_zettel_manager import SonnetZettelManagerWorker
from services.crank_streaming import StreamingWorker


# Worker registry - maps manifest worker_id to worker class
WORKER_REGISTRY = {
    "streaming": StreamingWorker,
    "email_classifier": EmailClassifierWorker,
    "email_parser": EmailParserWorker,
    "doc_converter": DocumentConverterWorker,
    "philosophical_analyzer": PhilosophicalAnalyzerWorker,
    "sonnet_zettel": SonnetZettelManagerWorker,
    "codex_zettel": CodexZettelRepositoryWorker,
    "hello_world": HelloWorldWorker,
}


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load capability manifest from YAML file."""
    with open(manifest_path) as f:
        return yaml.safe_load(f)


def get_manifest_files() -> list[Path]:
    """Get all capability manifest files."""
    manifests_dir = Path(__file__).parent / "manifests"
    return sorted(manifests_dir.glob("*.yaml"))


@pytest.mark.parametrize("manifest_file", get_manifest_files())
def test_worker_meets_capability_contract(manifest_file: Path) -> None:
    """Test worker provides all required capabilities per its manifest.

    This test validates:
    1. Worker provides minimum number of capabilities
    2. All required capabilities are present
    3. Capability versions meet minimum requirements
    4. Contract requirements are met (schemas, versioning, etc.)
    """
    # Load manifest
    manifest = load_manifest(manifest_file)
    worker_id = manifest["worker_id"]

    # Get worker instance
    worker_class = WORKER_REGISTRY.get(worker_id)
    if not worker_class:
        pytest.fail(
            f"Worker '{worker_id}' not found in registry. "
            f"Add it to WORKER_REGISTRY in test_capability_contracts.py"
        )

    worker = worker_class()
    actual_capabilities = worker.get_capabilities()

    # Test 1: Minimum capability count
    min_caps = manifest["minimum_capabilities"]
    assert len(actual_capabilities) >= min_caps, (
        f"Worker '{worker_id}' provides {len(actual_capabilities)} capabilities, "
        f"but manifest requires minimum {min_caps}"
    )

    # Test 2: Required capabilities present
    required_caps = manifest.get("required_capabilities", [])
    actual_cap_ids = {cap.id for cap in actual_capabilities}

    for required in required_caps:
        required_id = required["id"]
        assert required_id in actual_cap_ids, (
            f"Worker '{worker_id}' missing required capability: {required_id}\n"
            f"Available capabilities: {sorted(actual_cap_ids)}\n"
            f"Update worker to provide this capability or update manifest."
        )

        # Test 3: Version requirements
        if "version_min" in required:
            min_version = version.parse(required["version_min"])
            actual_cap = next(c for c in actual_capabilities if c.id == required_id)
            actual_version = version.parse(
                f"{actual_cap.version.major}.{actual_cap.version.minor}.{actual_cap.version.patch}"
            )

            assert actual_version >= min_version, (
                f"Capability '{required_id}' version {actual_version} "
                f"does not meet minimum {min_version}"
            )

        # Test 4: Expected tags (if specified)
        if "expected_tags" in required:
            actual_cap = next(c for c in actual_capabilities if c.id == required_id)
            actual_tags = getattr(actual_cap, "tags", [])
            expected_tags = required["expected_tags"]

            for expected_tag in expected_tags:
                assert expected_tag in actual_tags, (
                    f"Capability '{required_id}' missing expected tag: {expected_tag}\n"
                    f"Available tags: {actual_tags}"
                )

    # Test 5: Contract requirements
    contract_reqs = manifest.get("contract_requirements", {})

    if contract_reqs.get("all_capabilities_have_id"):
        for cap in actual_capabilities:
            assert cap.id, f"Capability missing ID: {cap}"

    if contract_reqs.get("all_capabilities_have_version"):
        for cap in actual_capabilities:
            assert cap.version, f"Capability {cap.id} missing version"

    if contract_reqs.get("all_capabilities_have_input_schema"):
        for cap in actual_capabilities:
            assert cap.contract.input_schema, (
                f"Capability {cap.id} missing input_schema"
            )

    if contract_reqs.get("all_capabilities_have_output_schema"):
        for cap in actual_capabilities:
            assert cap.contract.output_schema, (
                f"Capability {cap.id} missing output_schema"
            )

    # Test 6: Unexpected capabilities (warning mode)
    if not manifest.get("allow_additional_capabilities", True):
        expected_ids = {req["id"] for req in required_caps}
        unexpected = actual_cap_ids - expected_ids

        if unexpected:
            pytest.fail(
                f"Worker '{worker_id}' provides unexpected capabilities: {unexpected}\n"
                f"Either update manifest to allow these, or remove from worker.\n"
                f"Manifest location: {manifest_file}"
            )


def test_all_workers_have_manifests() -> None:
    """Test that every worker in the registry has a capability manifest.

    This ensures we don't forget to create manifests for new workers.
    """
    manifests_dir = Path(__file__).parent / "manifests"
    manifest_files = {f.stem for f in manifests_dir.glob("*.yaml")}

    for worker_id in WORKER_REGISTRY.keys():
        assert worker_id in manifest_files, (
            f"Worker '{worker_id}' missing capability manifest.\n"
            f"Create: tests/capabilities/manifests/{worker_id}.yaml"
        )


def test_manifest_schema_validity() -> None:
    """Test that all manifests follow the expected schema.

    Validates manifest structure to catch typos and missing fields.
    """
    required_fields = [
        "worker_id",
        "service_name",
        "default_port",
        "minimum_capabilities",
        "required_capabilities",
        "contract_requirements",
    ]

    for manifest_file in get_manifest_files():
        manifest = load_manifest(manifest_file)

        for field in required_fields:
            assert field in manifest, (
                f"Manifest {manifest_file.name} missing required field: {field}"
            )

        # Validate required_capabilities structure
        for cap in manifest["required_capabilities"]:
            assert "id" in cap, (
                f"Manifest {manifest_file.name}: required_capability missing 'id'"
            )
            assert "version_min" in cap, (
                f"Manifest {manifest_file.name}: required_capability missing 'version_min'"
            )


if __name__ == "__main__":
    print("Capability Contract Testing")
    print("=" * 80)
    print(f"Found {len(get_manifest_files())} manifests:")
    for manifest_file in get_manifest_files():
        manifest = load_manifest(manifest_file)
        print(f"  - {manifest['worker_id']:25} ({manifest['service_name']})")

    print("\nRun with: pytest tests/capabilities/test_capability_contracts.py -v")
