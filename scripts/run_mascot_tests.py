#!/usr/bin/env python3
"""
🎭 Mascot-Driven Testing Framework Orchestrator

This script coordinates testing across all architectural mascots,
allowing for single mascot testing, collaboration patterns, or
full council reviews.
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MascotType(Enum):
    WENDY = "wendy"     # 🐰 Zero-Trust Security Bunny
    KEVIN = "kevin"     # 🦙 Portability Llama  
    BELLA = "bella"     # 🐩 Modularity Poodle
    OLIVER = "oliver"   # 🦅 Anti-Pattern Eagle

@dataclass
class TestResult:
    mascot: MascotType
    target: str
    passed: bool
    score: float
    findings: List[str]
    recommendations: List[str]
    evidence: List[str]

@dataclass
class CollaborationPattern:
    mascots: Set[MascotType]
    name: str
    focus_areas: List[str]
    integration_points: List[str]

class MascotTestOrchestrator:
    """Coordinates testing across architectural mascots"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.mascots_dir = project_root / "mascots"
        self.results: Dict[MascotType, List[TestResult]] = {}
        
        # Define collaboration patterns
        self.collaboration_patterns = {
            "wendy+kevin": CollaborationPattern(
                mascots={MascotType.WENDY, MascotType.KEVIN},
                name="Secure Portability",
                focus_areas=["secure_runtime_abstraction", "encrypted_communication", "cert_portability"],
                integration_points=["mtls_across_runtimes", "secret_env_config"]
            ),
            "bella+oliver": CollaborationPattern(
                mascots={MascotType.BELLA, MascotType.OLIVER},
                name="Clean Architecture",
                focus_areas=["modular_patterns", "anti_pattern_prevention", "interface_quality"],
                integration_points=["service_separation_quality", "pattern_compliance"]
            ),
            "wendy+bella": CollaborationPattern(
                mascots={MascotType.WENDY, MascotType.BELLA},
                name="Secure Modularity",
                focus_areas=["security_boundaries", "isolated_services", "secure_interfaces"],
                integration_points=["service_isolation_security", "interface_validation"]
            ),
            "full_council": CollaborationPattern(
                mascots={MascotType.WENDY, MascotType.KEVIN, MascotType.BELLA, MascotType.OLIVER},
                name="Full Architectural Review",
                focus_areas=["comprehensive_analysis", "cross_cutting_concerns", "architectural_coherence"],
                integration_points=["all_mascot_alignment", "architectural_consensus"]
            )
        }
    
    def get_mascot_emoji(self, mascot: MascotType) -> str:
        """Get emoji representation for mascot"""
        emoji_map = {
            MascotType.WENDY: "🐰",
            MascotType.KEVIN: "🦙", 
            MascotType.BELLA: "🐩",
            MascotType.OLIVER: "🦅"
        }
        return emoji_map[mascot]
    
    def load_mascot_config(self, mascot: MascotType) -> Dict:
        """Load configuration for specific mascot"""
        config_file = self.mascots_dir / mascot.value / f"{mascot.value}_config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configurations
        default_configs = {
            MascotType.WENDY: {
                "test_categories": ["input_sanitization", "certificate_validation", "mtls", "secrets", "auth"],
                "severity_threshold": "high",
                "compliance_standards": ["OWASP", "NIST", "CWE"],
                "bobby_tables_patterns": True
            },
            MascotType.KEVIN: {
                "test_categories": ["runtime_abstraction", "environment_config", "platform_independence"],
                "target_runtimes": ["docker", "containerd", "kubernetes", "openshift"],
                "portability_score_minimum": 4.0
            },
            MascotType.BELLA: {
                "test_categories": ["service_boundaries", "interface_clarity", "dependency_injection"],
                "separation_score_minimum": 4.0,
                "plugin_architecture": True
            },
            MascotType.OLIVER: {
                "test_categories": ["anti_patterns", "solid_principles", "quality_metrics"],
                "evidence_required": True,
                "authoritative_sources": ["GoF", "Clean Code", "RFCs"]
            }
        }
        return default_configs[mascot]
    
    async def run_single_mascot_test(self, mascot: MascotType, target: str) -> TestResult:
        """Run tests for a single mascot"""
        emoji = self.get_mascot_emoji(mascot)
        logger.info(f"{emoji} {mascot.value.title()} starting analysis of {target}")
        
        config = self.load_mascot_config(mascot)
        test_script = self.mascots_dir / mascot.value / f"{mascot.value}_tests.py"
        
        if not test_script.exists():
            logger.warning(f"Test script not found for {mascot.value}: {test_script}")
            return TestResult(
                mascot=mascot,
                target=target,
                passed=False,
                score=0.0,
                findings=[f"Test script missing: {test_script}"],
                recommendations=[f"Create {mascot.value}_tests.py"],
                evidence=["File system check"]
            )
        
        # Simulate test execution (replace with actual test runner)
        findings, recommendations, evidence, score = await self._execute_mascot_tests(
            mascot, target, config
        )
        
        passed = score >= config.get('minimum_score', 3.0)
        
        result = TestResult(
            mascot=mascot,
            target=target,
            passed=passed,
            score=score,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence
        )
        
        logger.info(f"{emoji} {mascot.value.title()} completed: {score:.1f}/5.0 ({'PASS' if passed else 'FAIL'})")
        return result
    
    async def _execute_mascot_tests(self, mascot: MascotType, target: str, config: Dict) -> tuple:
        """Execute specific mascot test suite"""
        # This would integrate with actual test execution
        # For now, return mock results based on mascot type
        
        if mascot == MascotType.WENDY:
            findings = [
                "Input validation implemented with parameterized queries",
                "mTLS configured for all external communications",
                "Secret rotation policy in place"
            ]
            recommendations = [
                "Add rate limiting to API endpoints",
                "Implement additional CSRF protection"
            ]
            evidence = ["OWASP compliance check", "Security scan results"]
            score = 4.2
            
        elif mascot == MascotType.KEVIN:
            findings = [
                "Runtime detection logic present",
                "Environment-based configuration used",
                "No hardcoded Docker assumptions"
            ]
            recommendations = [
                "Add graceful fallback for unknown runtimes",
                "Enhance cross-platform testing"
            ]
            evidence = ["Portability analysis", "Runtime compatibility matrix"]
            score = 4.5
            
        elif mascot == MascotType.BELLA:
            findings = [
                "Clean service boundaries defined",
                "Dependency injection pattern used",
                "Plugin interface established"
            ]
            recommendations = [
                "Extract shared utilities to common library",
                "Improve interface documentation"
            ]
            evidence = ["Dependency analysis", "Interface review"]
            score = 4.0
            
        elif mascot == MascotType.OLIVER:
            findings = [
                "SOLID principles generally followed",
                "No obvious anti-patterns detected",
                "Code quality metrics within acceptable range"
            ]
            recommendations = [
                "Refactor large methods in EmailParser class",
                "Add more comprehensive unit test coverage"
            ]
            evidence = ["Static analysis report", "Complexity metrics", "Gang of Four pattern analysis"]
            score = 3.8
        
        return findings, recommendations, evidence, score
    
    async def run_collaboration_pattern(self, pattern_name: str, target: str) -> Dict[MascotType, TestResult]:
        """Run collaborative testing between specific mascots"""
        if pattern_name not in self.collaboration_patterns:
            raise ValueError(f"Unknown collaboration pattern: {pattern_name}")
        
        pattern = self.collaboration_patterns[pattern_name]
        logger.info(f"🤝 Running {pattern.name} collaboration on {target}")
        
        # Run individual mascot tests
        tasks = []
        for mascot in pattern.mascots:
            tasks.append(self.run_single_mascot_test(mascot, target))
        
        results = await asyncio.gather(*tasks)
        
        # Analyze collaboration points
        collaboration_results = {}
        for result in results:
            collaboration_results[result.mascot] = result
        
        # Log collaboration summary
        logger.info(f"🤝 {pattern.name} collaboration completed")
        for mascot, result in collaboration_results.items():
            emoji = self.get_mascot_emoji(mascot)
            logger.info(f"  {emoji} {mascot.value.title()}: {result.score:.1f}/5.0")
        
        return collaboration_results
    
    def generate_agent_prompt(self, mascot: MascotType, context: str = "") -> str:
        """Generate AI agent prompt for specific mascot"""
        prompt_file = self.mascots_dir / mascot.value / f"{mascot.value}_agent_prompt.txt"
        
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                base_prompt = f.read()
        else:
            # Fallback to default prompts from README
            base_prompt = self._get_default_prompt(mascot)
        
        if context:
            base_prompt += f"\n\nContext: {context}"
        
        return base_prompt
    
    def _get_default_prompt(self, mascot: MascotType) -> str:
        """Get default prompt for mascot (from README)"""
        prompts = {
            MascotType.WENDY: """You are now acting as Wendy the Zero-Trust Security Bunny, a detail-oriented security specialist who treats NIST recommendations as received holy wisdom and believes that people who fail to perform security commandments should be educated with extreme prejudice.""",
            MascotType.KEVIN: """You are now acting as Kevin the Portability Llama, an architectural purist who believes in "write once, run anywhere" with religious fervor.""",
            MascotType.BELLA: """You are now acting as Bella the Modularity Poodle, a perfectionist architect who believes in "loose coupling, high cohesion" with the precision of a Swiss watchmaker.""",
            MascotType.OLIVER: """You are now acting as Oliver the Anti-Pattern Eagle, a vigilant code quality guardian who spots architectural decay before it spreads like a disease."""
        }
        return prompts[mascot]
    
    def print_results_summary(self, results: Dict[MascotType, TestResult]):
        """Print formatted results summary"""
        print("\n" + "="*80)
        print("🎭 MASCOT TEST RESULTS SUMMARY")
        print("="*80)
        
        for mascot, result in results.items():
            emoji = self.get_mascot_emoji(mascot)
            status = "✅ PASS" if result.passed else "❌ FAIL"
            
            print(f"\n{emoji} {mascot.value.upper()} THE {mascot.name.split('.')[-1].title()}")
            print(f"   Status: {status} | Score: {result.score:.1f}/5.0")
            print(f"   Target: {result.target}")
            
            if result.findings:
                print("   Findings:")
                for finding in result.findings[:3]:  # Show top 3
                    print(f"     • {finding}")
            
            if result.recommendations:
                print("   Recommendations:")
                for rec in result.recommendations[:2]:  # Show top 2
                    print(f"     → {rec}")
        
        # Overall summary
        total_score = sum(r.score for r in results.values()) / len(results)
        passes = sum(1 for r in results.values() if r.passed)
        
        print(f"\n🎯 OVERALL ASSESSMENT")
        print(f"   Average Score: {total_score:.1f}/5.0")
        print(f"   Mascots Satisfied: {passes}/{len(results)}")
        
        if passes == len(results):
            print("   🎉 All mascots are happy! Architecture approved.")
        else:
            print("   ⚠️  Some mascots have concerns. Review recommendations.")
        
        print("="*80)

async def main():
    parser = argparse.ArgumentParser(description="🎭 Mascot-Driven Testing Framework")
    parser.add_argument("--target", help="Target file/directory to test")
    parser.add_argument("--mascot", choices=[m.value for m in MascotType], 
                       help="Run tests for specific mascot")
    parser.add_argument("--collaboration", choices=["wendy+kevin", "bella+oliver", "wendy+bella", "full_council"],
                       help="Run collaboration pattern")
    parser.add_argument("--council", action="store_true", help="Run full council review")
    parser.add_argument("--generate-prompt", metavar="MASCOT", choices=[m.value for m in MascotType],
                       help="Generate AI agent prompt for mascot")
    parser.add_argument("--context", help="Additional context for prompt generation")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    orchestrator = MascotTestOrchestrator(Path(args.project_root))
    
    # Handle prompt generation
    if args.generate_prompt:
        mascot = MascotType(args.generate_prompt)
        prompt = orchestrator.generate_agent_prompt(mascot, args.context or "")
        print(f"\n🎭 Agent Prompt for {orchestrator.get_mascot_emoji(mascot)} {mascot.value.title()}:")
        print("="*60)
        print(prompt)
        return
    
    # Handle testing
    if not args.target and not args.generate_prompt:
        print("❌ Please specify --target for testing or --generate-prompt for prompt generation")
        sys.exit(1)
    
    if args.council or args.collaboration == "full_council":
        results = await orchestrator.run_collaboration_pattern("full_council", args.target)
    elif args.collaboration:
        results = await orchestrator.run_collaboration_pattern(args.collaboration, args.target)
    elif args.mascot:
        mascot = MascotType(args.mascot)
        result = await orchestrator.run_single_mascot_test(mascot, args.target)
        results = {mascot: result}
    elif args.target:
        print("❌ Please specify --mascot, --collaboration, or --council")
        sys.exit(1)
    else:
        return  # No testing to do, just prompt generation
    
    orchestrator.print_results_summary(results)

if __name__ == "__main__":
    asyncio.run(main())