#!/bin/bash
set -e

echo "🔍 Crank Platform Environment Validation"
echo "========================================"
echo "Checking if environment is ready for PaaS layer deployment..."
echo ""

# Check if we're in the right directory
if [[ ! -f "services/mesh_interface_v2.py" ]]; then
    echo "❌ Must be run from crank-platform root directory"
    exit 1
fi

# Track validation results
VALIDATION_PASSED=true
MISSING_REQUIREMENTS=()

# Function to check command availability
check_command() {
    local cmd=$1
    local name=$2
    
    if command -v "$cmd" &> /dev/null; then
        echo "✅ $name: Found"
        return 0
    else
        echo "❌ $name: Not found"
        MISSING_REQUIREMENTS+=("$name")
        VALIDATION_PASSED=false
        return 1
    fi
}

echo "📋 Essential Platform Requirements:"
echo "-----------------------------------"

# Core requirements for platform layer
check_command "docker" "Docker"
check_command "python3.12" "Python 3.12"
check_command "uv" "uv (Python package manager)"

# Docker compose
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        echo "✅ Docker Compose: Available"
    else
        echo "❌ Docker Compose: Not available"
        MISSING_REQUIREMENTS+=("Docker Compose")
        VALIDATION_PASSED=false
    fi
fi

echo ""
echo "🐍 Python Environment:"
echo "----------------------"

# Check if virtual environment exists
if [[ -d ".venv" ]]; then
    echo "✅ Virtual environment: Found (.venv)"
    
    # Check if requirements are installed
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        # Try to activate and check key packages
        source .venv/bin/activate 2>/dev/null || true
        
        if python -c "import fastapi, pydantic, httpx" 2>/dev/null; then
            echo "✅ Platform dependencies: Installed"
        else
            echo "❌ Platform dependencies: Missing"
            MISSING_REQUIREMENTS+=("Python dependencies")
            VALIDATION_PASSED=false
        fi
    fi
else
    echo "❌ Virtual environment: Not found"
    MISSING_REQUIREMENTS+=("Python virtual environment")
    VALIDATION_PASSED=false
fi

echo ""
echo "🏗️ Infrastructure Layer Check:"
echo "------------------------------"

# Check if crank-infrastructure is available
INFRA_PATH="../crank-infrastructure"
if [[ -d "$INFRA_PATH" ]]; then
    echo "✅ crank-infrastructure: Found at $INFRA_PATH"
    
    if [[ -x "$INFRA_PATH/setup.sh" ]]; then
        echo "✅ Infrastructure setup: Available"
    else
        echo "⚠️ Infrastructure setup: Not executable"
    fi
    
    if [[ -x "$INFRA_PATH/tools/validation/check-platform-requirements.sh" ]]; then
        echo "✅ Infrastructure validation: Available"
    else
        echo "⚠️ Infrastructure validation: Not found"
    fi
else
    echo "❌ crank-infrastructure: Not found"
    echo "   Clone from: https://github.com/crankbird/crank-infrastructure"
    MISSING_REQUIREMENTS+=("crank-infrastructure repository")
    VALIDATION_PASSED=false
fi

echo ""
echo "📊 Platform Health Check:"
echo "========================="

if [[ $VALIDATION_PASSED == true ]]; then
    echo "🎉 Platform environment validation PASSED!"
    echo "✅ All requirements met for PaaS layer deployment"
    
    echo ""
    echo "🚀 Ready to start platform services:"
    echo "• Diagnostic mesh: docker-compose -f docker-compose.refactored-mesh.yml up"
    echo "• Full platform: docker-compose up"
    echo "• Test mesh: python test-refactored-mesh.py"
    
else
    echo "⚠️ Platform environment validation FAILED"
    echo "❌ Missing requirements:"
    echo ""
    for req in "${MISSING_REQUIREMENTS[@]}"; do
        echo "   • $req"
    done
    
    echo ""
    echo "🔧 To fix missing requirements:"
    
    if [[ ! -d "$INFRA_PATH" ]]; then
        echo "1. Clone infrastructure layer:"
        echo "   git clone https://github.com/crankbird/crank-infrastructure ../crank-infrastructure"
        echo ""
    fi
    
    echo "2. Set up infrastructure:"
    echo "   cd ../crank-infrastructure && ./setup.sh --environment ai-ml"
    echo ""
    echo "3. Set up platform environment:"
    echo "   cd ../crank-platform && uv venv .venv && source .venv/bin/activate"
    echo "   uv pip install -r requirements.txt"
    echo ""
    echo "4. Re-run this validation:"
    echo "   ./scripts/validate-environment.sh"
fi

echo ""
echo "🔗 Architecture Layers:"
echo "• IaaS: crank-infrastructure (environment setup, containers, VMs)"  
echo "• PaaS: crank-platform (this repo - service mesh, security, governance)"
echo "• SaaS: crankdoc, parse-email-archive (business logic services)"

echo ""
echo "📚 Resources:"
echo "• Platform docs: ./README.md"
echo "• Mesh interface: ./services/mesh_interface_v2.py" 
echo "• Infrastructure setup: ../crank-infrastructure/README.md"

# Exit with appropriate code
if [[ $VALIDATION_PASSED == true ]]; then
    exit 0
else
    exit 1
fi