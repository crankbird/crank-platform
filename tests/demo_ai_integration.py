#!/usr/bin/env python3
"""
🎭 Mascot Agent Integration Demo

This script demonstrates how to integrate AI agents with the mascot-driven
testing framework, showing how to invoke specific architectural perspectives
using AI models.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List

# Import the mascot orchestrator
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_mascot_tests import MascotTestOrchestrator, MascotType

def simulate_ai_agent_call(prompt: str, context: str = "") -> Dict:
    """
    Simulate calling an AI agent with the mascot prompt.
    In production, this would integrate with actual AI services like:
    - OpenAI GPT-4
    - Azure OpenAI
    - Anthropic Claude
    - Local LLM via Ollama
    """

    # Extract mascot from prompt
    mascot_name = "Unknown"
    if "Wendy" in prompt:
        mascot_name = "Wendy the Zero-Trust Security Bunny"
        analysis_focus = "security vulnerabilities and Bobby Tables prevention"
    elif "Kevin" in prompt:
        mascot_name = "Kevin the Portability Llama"
        analysis_focus = "platform independence and runtime portability"
    elif "Bella" in prompt:
        mascot_name = "Bella the Modularity Poodle"
        analysis_focus = "service separation and interface design"
    elif "Oliver" in prompt:
        mascot_name = "Oliver the Anti-Pattern Eagle"
        analysis_focus = "code quality and architectural patterns"

    # Simulate AI response based on mascot personality
    simulated_response = {
        "agent": mascot_name,
        "analysis": f"I've reviewed the code with focus on {analysis_focus}.",
        "findings": [
            f"Code analysis completed from {mascot_name.split()[0]}'s perspective",
            "Detailed findings would appear here in production",
            "AI agent would provide specific recommendations"
        ],
        "recommendations": [
            f"Follow {mascot_name.split()[0]}'s architectural principles",
            "Implement suggested improvements",
            "Review compliance with relevant standards"
        ],
        "confidence": 0.85,
        "context_used": context
    }

    return simulated_response

async def demo_single_mascot_ai_review(orchestrator: MascotTestOrchestrator,
                                     target_file: str, mascot: MascotType):
    """Demonstrate AI-powered single mascot review"""

    print(f"\n{'='*80}")
    print(f"🎭 SINGLE MASCOT AI REVIEW DEMO")
    print(f"{'='*80}")

    # Generate the AI prompt for the mascot
    context = f"Reviewing {target_file} for architectural compliance"
    prompt = orchestrator.generate_agent_prompt(mascot, context)

    print(f"🤖 Invoking AI agent with {orchestrator.get_mascot_emoji(mascot)} {mascot.value.title()}'s prompt...")

    # Simulate AI agent call
    ai_response = simulate_ai_agent_call(prompt, context)

    # Also run the automated test suite
    test_result = await orchestrator.run_single_mascot_test(mascot, target_file)

    # Combine AI and automated results
    print(f"\n📋 COMBINED ANALYSIS RESULTS:")
    print(f"Agent: {ai_response['agent']}")
    print(f"Automated Score: {test_result.score}/5.0")
    print(f"AI Confidence: {ai_response['confidence']:.0%}")

    print(f"\n🔍 AI Findings:")
    for finding in ai_response['findings']:
        print(f"  • {finding}")

    print(f"\n🎯 Automated Findings:")
    for finding in test_result.findings[:3]:
        print(f"  • {finding}")

    print(f"\n💡 Combined Recommendations:")
    combined_recs = list(set(ai_response['recommendations'] + test_result.recommendations))
    for rec in combined_recs[:3]:
        print(f"  → {rec}")

async def demo_collaboration_ai_review(orchestrator: MascotTestOrchestrator,
                                     target_file: str, mascots: List[MascotType]):
    """Demonstrate AI-powered mascot collaboration"""

    print(f"\n{'='*80}")
    print(f"🤝 MASCOT COLLABORATION AI REVIEW DEMO")
    print(f"{'='*80}")

    ai_responses = {}
    test_results = {}

    # Get each mascot's perspective
    for mascot in mascots:
        context = f"Collaborative review of {target_file} - focus on {mascot.value} concerns"
        prompt = orchestrator.generate_agent_prompt(mascot, context)

        print(f"🤖 Consulting {orchestrator.get_mascot_emoji(mascot)} {mascot.value.title()}...")

        # Simulate AI responses
        ai_responses[mascot] = simulate_ai_agent_call(prompt, context)

        # Get automated test results
        test_results[mascot] = await orchestrator.run_single_mascot_test(mascot, target_file)

    # Analyze collaboration
    print(f"\n🏛️ ARCHITECTURAL COUNCIL CONSENSUS:")

    total_score = sum(result.score for result in test_results.values()) / len(test_results)
    avg_confidence = sum(response['confidence'] for response in ai_responses.values()) / len(ai_responses)

    print(f"Overall Architectural Score: {total_score:.1f}/5.0")
    print(f"AI Consensus Confidence: {avg_confidence:.0%}")

    # Check for conflicts or agreements
    print(f"\n🔄 CROSS-CUTTING CONCERNS:")
    if total_score >= 4.0 and avg_confidence >= 0.8:
        print("✅ Strong consensus - architecture approved by council")
    elif total_score >= 3.0:
        print("⚠️  Mixed feedback - some concerns need addressing")
    else:
        print("❌ Council rejection - significant architectural issues detected")

    print(f"\n📊 INDIVIDUAL MASCOT ASSESSMENTS:")
    for mascot in mascots:
        emoji = orchestrator.get_mascot_emoji(mascot)
        score = test_results[mascot].score
        confidence = ai_responses[mascot]['confidence']
        status = "✅" if score >= 4.0 and confidence >= 0.8 else "⚠️"

        print(f"  {status} {emoji} {mascot.value.title()}: {score:.1f}/5.0 (AI: {confidence:.0%})")

def demo_prompt_customization():
    """Demonstrate how to customize mascot prompts for specific contexts"""

    print(f"\n{'='*80}")
    print(f"🎨 PROMPT CUSTOMIZATION DEMO")
    print(f"{'='*80}")

    # Custom context examples
    contexts = [
        "microservices security audit",
        "container orchestration review",
        "API gateway design evaluation",
        "database access pattern analysis"
    ]

    orchestrator = MascotTestOrchestrator(Path("."))

    for context in contexts:
        print(f"\n📝 Context: {context}")

        # Show how each mascot's prompt adapts
        for mascot in [MascotType.WENDY, MascotType.KEVIN]:
            prompt = orchestrator.generate_agent_prompt(mascot, context)

            # Extract the context addition (last line)
            prompt_lines = prompt.split('\n')
            context_line = prompt_lines[-1] if prompt_lines[-1].startswith("Context:") else "No context added"

            emoji = orchestrator.get_mascot_emoji(mascot)
            print(f"  {emoji} {mascot.value.title()}: {context_line}")

async def main():
    """Main demo function"""

    print("🎭 MASCOT-DRIVEN AI TESTING FRAMEWORK DEMO")
    print("="*80)
    print("This demo shows how to integrate AI agents with architectural mascots")
    print("for comprehensive code quality assessment.\n")

    # Setup
    project_root = Path(".")
    orchestrator = MascotTestOrchestrator(project_root)

    # Find a test file
    test_files = list(project_root.glob("**/*.py"))
    target_file = str(test_files[0]) if test_files else "example_file.py"

    print(f"🎯 Target for analysis: {target_file}")

    # Demo 1: Single mascot AI review
    await demo_single_mascot_ai_review(orchestrator, target_file, MascotType.WENDY)

    # Demo 2: Collaboration review
    collaboration_mascots = [MascotType.WENDY, MascotType.KEVIN]
    await demo_collaboration_ai_review(orchestrator, target_file, collaboration_mascots)

    # Demo 3: Prompt customization
    demo_prompt_customization()

    print(f"\n{'='*80}")
    print("🎉 DEMO COMPLETE")
    print("="*80)
    print("This framework enables:")
    print("  • AI agents with specific architectural perspectives")
    print("  • Automated testing combined with AI analysis")
    print("  • Collaborative reviews across multiple concerns")
    print("  • Context-aware prompt generation")
    print("  • Consistent architectural standards enforcement")
    print("\n🚀 Ready for production integration with:")
    print("  • OpenAI GPT-4 / Azure OpenAI")
    print("  • Anthropic Claude")
    print("  • Local LLMs via Ollama")
    print("  • Custom fine-tuned models")

if __name__ == "__main__":
    asyncio.run(main())
