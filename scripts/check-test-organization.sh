#!/bin/bash
# check-test-organization.sh
# Validates that test files are in the correct directories

set -e

echo "🔍 Checking Test Organization"
echo "============================"

VIOLATIONS=0

# Check for test files in scripts/
echo "Checking for test files in scripts/ directory..."
if find scripts/ -name "test*.py" -o -name "*test*.py" -o -name "test*.sh" | grep -q .; then
    echo "❌ Found test files in scripts/ directory:"
    find scripts/ -name "test*.py" -o -name "*test*.py" -o -name "test*.sh"
    echo "   → Move these to tests/ directory"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ No test files found in scripts/"
fi

# Check for operational scripts in tests/
echo "Checking for operational scripts in tests/ directory..."
OPERATIONAL_PATTERNS="install|setup|deploy|start|stop|generate|validate|check"
if find tests/ -name "*.sh" | grep -E "(${OPERATIONAL_PATTERNS})" | grep -q .; then
    echo "❌ Found operational scripts in tests/ directory:"
    find tests/ -name "*.sh" | grep -E "(${OPERATIONAL_PATTERNS})"
    echo "   → Move these to scripts/ directory"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ No operational scripts found in tests/"
fi

if [[ $VIOLATIONS -eq 0 ]]; then
    echo ""
    echo "🎉 Test organization is correct!"
    echo "   tests/ = Test code only"
    echo "   scripts/ = Operational utilities only"
else
    echo ""
    echo "⚠️  Found $VIOLATIONS organization violations"
    echo "   Please move files to the correct directories"
    exit 1
fi