#!/bin/bash
# 🎭 Mascot Framework Context Loader
# 
# This script opens all essential mascot framework files to establish 
# AI assistant context on a new machine.

echo "🎭 Loading Mascot Framework Context for AI Assistants..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "run_mascot_tests.py" ]; then
    echo "❌ Error: Please run this from the crank-platform root directory"
    exit 1
fi

echo "📂 Opening core mascot documentation..."

# Core documentation files
if command -v code &> /dev/null; then
    echo "  🎯 Using VS Code..."
    
    # Essential mascot files
    code docs/ARCHITECTURAL_MENAGERIE_GUIDE.md
    code docs/MASCOT_HAPPINESS_REPORT.md
    code ENHANCED_MASCOT_FRAMEWORK.md
    code mascots/README.md
    code AI_ASSISTANT_ONBOARDING.md
    
    # Mascot personalities
    code mascots/wendy/wendy_agent_prompt.txt
    code mascots/kevin/kevin_agent_prompt.txt
    
    # Framework tools
    code run_mascot_tests.py
    code demo_ai_integration.py
    
    # Test examples
    code mascots/wendy/wendy_tests.py
    code mascots/kevin/kevin_tests.py
    
    echo "✅ Files opened in VS Code"
    
elif command -v vim &> /dev/null; then
    echo "  🎯 Using Vim..."
    vim -O docs/ARCHITECTURAL_MENAGERIE_GUIDE.md mascots/README.md
    
elif command -v nano &> /dev/null; then
    echo "  🎯 Files available for nano..."
    echo "     Run: nano docs/ARCHITECTURAL_MENAGERIE_GUIDE.md"
    
else
    echo "  📝 No editor detected. Key files to open manually:"
    echo "     docs/ARCHITECTURAL_MENAGERIE_GUIDE.md"
    echo "     docs/MASCOT_HAPPINESS_REPORT.md"
    echo "     mascots/README.md"
fi

echo ""
echo "🤖 Testing AI context establishment..."

# Test the framework
if python3 -c "import sys; sys.path.append('.'); from run_mascot_tests import MascotTestOrchestrator" 2>/dev/null; then
    echo "✅ Framework import successful"
    
    # Generate a test prompt
    echo "🎭 Generating test prompt for Wendy..."
    python3 run_mascot_tests.py --generate-prompt wendy --context "new machine onboarding test" | head -10
    
else
    echo "⚠️  Framework import failed - check Python dependencies"
fi

echo ""
echo "📋 Context Establishment Checklist:"
echo "  1. 📖 Core documentation loaded"
echo "  2. 🎭 Mascot personalities available"  
echo "  3. 🔧 Framework tools accessible"
echo "  4. 🧪 Test examples visible"
echo ""
echo "🎯 Copy this into your AI assistant to establish context:"
echo "=================================================="
cat << 'EOF'
MASCOT FRAMEWORK CONTEXT:
This codebase uses a mascot-driven architectural testing framework with 4 core mascots:

🐰 WENDY - Zero-Trust Security Bunny
- Domain: Security, OWASP compliance, Bobby Tables prevention
- Standards: NIST SP 800-53, zero-trust principles
- Focus: Input validation, mTLS, secrets management, injection prevention

🦙 KEVIN - Portability Llama  
- Domain: Platform independence, runtime abstraction
- Standards: 12-factor app, container runtime agnostic
- Focus: Environment config, multi-runtime support, vendor lock-in prevention

🐩 BELLA - Modularity Poodle
- Domain: Service separation, clean interfaces
- Standards: SOLID principles, dependency injection
- Focus: Loose coupling, high cohesion, plugin architecture

🦅 OLIVER - Anti-Pattern Eagle
- Domain: Code quality, architectural patterns
- Standards: Gang of Four, Clean Code, evidence-based decisions
- Focus: Anti-pattern detection, SOLID compliance, technical debt prevention

Bobby Tables is NOT a separate mascot - it's a vulnerability pattern under Wendy's security domain.

When reviewing code, consider which mascot's concerns are relevant and apply their standards.
EOF

echo "=================================================="
echo ""
echo "🎉 Mascot Framework context loaded!"
echo "   Your AI assistant should now understand the mascot architecture."
echo ""
echo "🧪 Test AI understanding with:"
echo "   'What would Wendy think about this SQL query?'"
echo "   'How would Kevin evaluate Docker dependencies?'"
echo "   'Which mascot handles Bobby Tables attacks?'"