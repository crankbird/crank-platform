#!/usr/bin/env python3
"""
Update Dockerfiles to match build manifests

This script reads the build manifests and updates all Dockerfiles to:
- Use services/ prefix for all COPY commands
- Reference the correct renamed files
- Match the standardized file structure
"""

import json
import re
from pathlib import Path


def update_dockerfile_for_service(service_name: str, manifest: dict):
    """Update a Dockerfile based on its build manifest"""
    dockerfile_path = Path(manifest["dockerfile"])

    if not dockerfile_path.exists():
        print(f"❌ Dockerfile not found: {dockerfile_path}")
        return

    with open(dockerfile_path) as f:
        content = f.read()

    print(f"🔧 Updating {dockerfile_path}")

    # Update requirements file reference
    req_file = manifest["dependencies"]["requirements_file"]
    req_filename = Path(req_file).name
    content = re.sub(
        rf"COPY {req_filename}",
        f"COPY {req_file}",
        content,
    )

    # Update runtime files
    for runtime_file in manifest["dependencies"]["runtime_files"]:
        filename = Path(runtime_file).name

        # Handle renamed files
        old_patterns = [
            rf"COPY {filename}",
            r"COPY initialize_certificates\.py",  # Old name
            rf"COPY services/{filename}",  # Already has services/ prefix
        ]

        for pattern in old_patterns:
            content = re.sub(pattern, f"COPY {runtime_file}", content)

    # Update configuration files
    for config_file in manifest["dependencies"].get("configuration_files", []):
        filename = Path(config_file).name
        content = re.sub(
            rf"COPY {filename}",
            f"COPY {config_file}",
            content,
        )

    # Special handling for plugin.yaml references
    if "plugin.yaml" in content:
        content = re.sub(
            r"COPY (.*\.plugin\.yaml) \./plugin\.yaml",
            r"COPY services/\1 ./plugin.yaml",
            content,
        )

    # Remove any duplicate services/ prefixes
    content = re.sub(r"COPY services/services/", "COPY services/", content)

    # Write updated content
    with open(dockerfile_path, "w") as f:
        f.write(content)

    print(f"✅ Updated {dockerfile_path}")


def main():
    services_dir = Path("services")

    # Load all manifests
    manifests = {}
    for manifest_file in services_dir.glob("*.build.json"):
        with open(manifest_file) as f:
            manifest = json.load(f)
            service_name = manifest["service"]
            manifests[service_name] = manifest

    print("🏗️ Updating Dockerfiles to match build manifests")
    print(f"📦 Found {len(manifests)} services")

    for service_name, manifest in manifests.items():
        update_dockerfile_for_service(service_name, manifest)

    print("\n✅ All Dockerfiles updated!")
    print("🚀 Ready to build with standardized file references")


if __name__ == "__main__":
    main()
