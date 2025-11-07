#!/usr/bin/env python3
"""
Parse smoke test results and prepare for issue creation.
"""

import json
import os
import sys


def main():
    try:
        with open("smoke_test_results.json") as f:
            results = json.load(f)

        warnings = results.get("warnings", [])

        # Create environment variable for warnings count
        github_output = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
        with open(github_output, "a") as f:
            f.write(f"warnings_count={len(warnings)}\n")

        # Save warnings to file for issue creation
        if warnings:
            with open("warnings.json", "w") as f:
                json.dump(warnings, f, indent=2)
            print(f"Found {len(warnings)} warnings to process")
        else:
            print("No warnings found")

    except Exception as e:
        print(f"Error parsing results: {e}")
        github_output = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
        with open(github_output, "a") as f:
            f.write("warnings_count=0\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
