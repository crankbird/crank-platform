#!/usr/bin/env python3
"""
🦙 Kevin's Portability Test Suite

Kevin the Portability Llama's comprehensive platform independence testing framework.
Ensures "write once, run anywhere" philosophy across all container runtimes.

Kevin's Philosophy:
"Platform independence is not optional. Vendor lock-in is the enemy of innovation.
If your code assumes Docker, you have failed the portability test."
"""

import docker
import json
import os
import re
import subprocess
import sys
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)

@dataclass
class PortabilityFinding:
    severity: str  # critical, high, medium, low
    category: str
    description: str
    file_path: str
    line_number: Optional[int]
    evidence: str
    platform_assumption: Optional[str] = None
    suggested_abstraction: Optional[str] = None

class KevinPortabilityAnalyzer:
    """🦙 Kevin's Portability Analysis Engine"""
    
    def __init__(self):
        self.findings: List[PortabilityFinding] = []
        self.supported_runtimes = ["docker", "containerd", "cri-o", "podman", "kubernetes", "openshift"]
        self.platform_assumptions = self._load_platform_assumptions()
        self.abstraction_patterns = self._load_abstraction_patterns()
    
    def _load_platform_assumptions(self) -> Dict[str, List[str]]:
        """Load platform-specific assumptions that violate portability"""
        return {
            "docker_specific": [
                r"docker\s+run",
                r"docker\s+build",
                r"docker\s+exec",
                r"docker\s+ps",
                r"DOCKER_HOST",
                r"docker\.sock",
                r"/var/run/docker\.sock"
            ],
            "kubernetes_specific": [
                r"kubectl\s+",
                r"kubernetes\.io",
                r"k8s\.io",
                r"\.kube/config",
                r"KUBECONFIG"
            ],
            "linux_specific": [
                r"/proc/",
                r"/sys/",
                r"/dev/",
                r"systemctl",
                r"systemd",
                r"apt-get",
                r"yum\s+",
                r"dnf\s+"
            ],
            "windows_specific": [
                r"C:\\",
                r"\.exe",
                r"cmd\.exe",
                r"powershell",
                r"registry",
                r"HKEY_"
            ],
            "hardcoded_paths": [
                r"/usr/local/",
                r"/opt/",
                r"/var/log/",
                r"/tmp/",
                r"C:\\Program Files",
                r"C:\\Windows"
            ],
            "network_assumptions": [
                r"localhost",
                r"127\.0\.0\.1",
                r"::1",
                r"\.local",
                r"host\.docker\.internal"
            ]
        }
    
    def _load_abstraction_patterns(self) -> Dict[str, str]:
        """Load recommended abstraction patterns"""
        return {
            "container_runtime": "Use container runtime interface (CRI) abstraction",
            "file_paths": "Use environment variables or config files for paths",
            "network_endpoints": "Use service discovery or environment-based configuration",
            "platform_detection": "Implement runtime detection with graceful fallbacks",
            "resource_access": "Use standard APIs and avoid direct system calls",
            "configuration": "Use 12-factor app configuration principles"
        }
    
    def analyze_file(self, file_path: Path) -> List[PortabilityFinding]:
        """🦙 Kevin's comprehensive portability analysis"""
        findings = []
        
        if not file_path.exists():
            return findings
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Platform Assumption Detection
            findings.extend(self._detect_platform_assumptions(file_path, content))
            
            # Container Runtime Analysis
            findings.extend(self._analyze_container_runtime(file_path, content))
            
            # Configuration Portability
            findings.extend(self._analyze_configuration(file_path, content))
            
            # Environment Variable Usage
            findings.extend(self._analyze_environment_variables(file_path, content))
            
            # Path Portability
            findings.extend(self._analyze_path_usage(file_path, content))
            
            # Network Portability
            findings.extend(self._analyze_network_configuration(file_path, content))
            
        except Exception as e:
            logger.error(f"🦙 Kevin encountered error analyzing {file_path}: {e}")
            findings.append(PortabilityFinding(
                severity="medium",
                category="analysis_error",
                description=f"Could not analyze file: {e}",
                file_path=str(file_path),
                line_number=None,
                evidence=str(e)
            ))
        
        return findings
    
    def _detect_platform_assumptions(self, file_path: Path, content: str) -> List[PortabilityFinding]:
        """🦙 Detect platform-specific assumptions"""
        findings = []
        lines = content.split('\n')
        
        for category, patterns in self.platform_assumptions.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        severity = "critical" if "hardcoded" in category else "high"
                        
                        findings.append(PortabilityFinding(
                            severity=severity,
                            category=f"platform_assumption_{category}",
                            description=f"Platform-specific assumption detected: {category.replace('_', ' ').title()}",
                            file_path=str(file_path),
                            line_number=line_num,
                            evidence=line.strip(),
                            platform_assumption=category,
                            suggested_abstraction=self._get_abstraction_suggestion(category)
                        ))
        
        return findings
    
    def _analyze_container_runtime(self, file_path: Path, content: str) -> List[PortabilityFinding]:
        """🦙 Analyze container runtime portability"""
        findings = []
        lines = content.split('\n')
        
        # Docker-specific patterns that should be abstracted
        docker_violations = [
            (r"docker\s+", "Direct Docker command usage", "Use container runtime abstraction"),
            (r"FROM\s+.*", "Dockerfile without multi-arch support", "Add multi-architecture support"),
            (r"COPY\s+.*", "File copy without path abstraction", "Use environment-based paths"),
            (r"ENV\s+DOCKER", "Docker-specific environment variables", "Use runtime-agnostic variables")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, suggestion in docker_violations:
                if re.search(pattern, line):
                    findings.append(PortabilityFinding(
                        severity="high",
                        category="container_runtime_coupling",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        suggested_abstraction=suggestion
                    ))
        
        return findings
    
    def _analyze_configuration(self, file_path: Path, content: str) -> List[PortabilityFinding]:
        """🦙 Analyze configuration portability"""
        findings = []
        
        if file_path.suffix in ['.yml', '.yaml']:
            try:
                config = yaml.safe_load(content)
                findings.extend(self._analyze_yaml_config(file_path, config))
            except yaml.YAMLError:
                pass
        
        if file_path.suffix == '.json':
            try:
                config = json.loads(content)
                findings.extend(self._analyze_json_config(file_path, config))
            except json.JSONDecodeError:
                pass
        
        return findings
    
    def _analyze_yaml_config(self, file_path: Path, config: Dict) -> List[PortabilityFinding]:
        """🦙 Analyze YAML configuration for portability issues"""
        findings = []
        
        def check_nested_config(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check for hardcoded values
                    if isinstance(value, str):
                        if any(pattern in value.lower() for pattern in ['docker', 'localhost', '/usr/', 'c:\\']):
                            findings.append(PortabilityFinding(
                                severity="medium",
                                category="hardcoded_config_value",
                                description=f"Hardcoded platform-specific value in {current_path}",
                                file_path=str(file_path),
                                line_number=None,
                                evidence=f"{key}: {value}",
                                suggested_abstraction="Use environment variable or template"
                            ))
                    
                    check_nested_config(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_nested_config(item, f"{path}[{i}]")
        
        check_nested_config(config)
        return findings
    
    def _analyze_json_config(self, file_path: Path, config: Dict) -> List[PortabilityFinding]:
        """🦙 Analyze JSON configuration for portability issues"""
        # Similar logic to YAML analysis
        return self._analyze_yaml_config(file_path, config)
    
    def _analyze_environment_variables(self, file_path: Path, content: str) -> List[PortabilityFinding]:
        """🦙 Analyze environment variable usage"""
        findings = []
        lines = content.split('\n')
        
        # Look for hardcoded values that should be environment variables
        hardcoded_patterns = [
            (r"host\s*=\s*['\"]localhost['\"]", "Hardcoded hostname", "Use HOST environment variable"),
            (r"port\s*=\s*\d+", "Hardcoded port", "Use PORT environment variable"),
            (r"database\s*=\s*['\"][^'\"]+['\"]", "Hardcoded database name", "Use DATABASE_URL environment variable"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password", "Use environment variable for secrets")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, suggestion in hardcoded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(PortabilityFinding(
                        severity="medium",
                        category="hardcoded_configuration",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        suggested_abstraction=suggestion
                    ))
        
        return findings
    
    def _analyze_path_usage(self, file_path: Path, content: str) -> List[PortabilityFinding]:
        """🦙 Analyze file path portability"""
        findings = []
        lines = content.split('\n')
        
        # Platform-specific path patterns
        path_violations = [
            (r"/usr/local/", "Unix-specific path", "Use configurable path or environment variable"),
            (r"C:\\", "Windows-specific path", "Use os.path or pathlib for cross-platform paths"),
            (r"/var/log/", "Unix-specific log path", "Use LOG_DIR environment variable"),
            (r"\\", "Windows path separator", "Use os.path.join() or pathlib.Path")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, suggestion in path_violations:
                if re.search(pattern, line):
                    findings.append(PortabilityFinding(
                        severity="medium",
                        category="platform_specific_path",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        suggested_abstraction=suggestion
                    ))
        
        return findings
    
    def _analyze_network_configuration(self, file_path: Path, content: str) -> List[PortabilityFinding]:
        """🦙 Analyze network configuration portability"""
        findings = []
        lines = content.split('\n')
        
        # Network assumption patterns
        network_violations = [
            (r"localhost", "Hardcoded localhost", "Use service discovery or environment variable"),
            (r"127\.0\.0\.1", "Hardcoded loopback IP", "Use service name or environment variable"),
            (r"host\.docker\.internal", "Docker-specific hostname", "Use portable service discovery"),
            (r"\.local", "mDNS dependency", "Use explicit service configuration")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, suggestion in network_violations:
                if re.search(pattern, line):
                    findings.append(PortabilityFinding(
                        severity="medium",
                        category="network_assumption",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        suggested_abstraction=suggestion
                    ))
        
        return findings
    
    def _get_abstraction_suggestion(self, category: str) -> str:
        """🦙 Get abstraction suggestion for category"""
        suggestions = {
            "docker_specific": "Use container runtime interface (CRI) abstraction",
            "kubernetes_specific": "Use cloud-native API abstraction",
            "linux_specific": "Use cross-platform libraries or runtime detection",
            "windows_specific": "Use cross-platform libraries or runtime detection",
            "hardcoded_paths": "Use environment variables or configuration files",
            "network_assumptions": "Use service discovery or environment-based configuration"
        }
        return suggestions.get(category, "Implement platform abstraction layer")
    
    def check_runtime_compatibility(self, target_path: Path) -> Dict[str, bool]:
        """🦙 Check compatibility with different container runtimes"""
        compatibility = {}
        
        for runtime in self.supported_runtimes:
            compatibility[runtime] = self._test_runtime_compatibility(target_path, runtime)
        
        return compatibility
    
    def _test_runtime_compatibility(self, target_path: Path, runtime: str) -> bool:
        """🦙 Test compatibility with specific runtime"""
        # Simplified compatibility check
        # In real implementation, this would run actual tests
        
        findings = []
        if target_path.is_file():
            findings.extend(self.analyze_file(target_path))
        else:
            for file in target_path.rglob("*"):
                if file.is_file():
                    findings.extend(self.analyze_file(file))
        
        # Check for runtime-specific violations
        runtime_violations = [f for f in findings if runtime.replace('-', '_') in f.category]
        
        return len(runtime_violations) == 0
    
    def generate_portability_report(self, target_path: Path) -> Dict:
        """🦙 Generate comprehensive portability report"""
        all_findings = []
        
        if target_path.is_file():
            all_findings.extend(self.analyze_file(target_path))
        else:
            # Analyze all relevant files
            for pattern in ["*.py", "*.yml", "*.yaml", "*.json", "Dockerfile*", "*.sh"]:
                for file in target_path.rglob(pattern):
                    all_findings.extend(self.analyze_file(file))
        
        # Runtime compatibility check
        runtime_compatibility = self.check_runtime_compatibility(target_path)
        
        # Categorize findings
        critical = [f for f in all_findings if f.severity == "critical"]
        high = [f for f in all_findings if f.severity == "high"]
        medium = [f for f in all_findings if f.severity == "medium"]
        low = [f for f in all_findings if f.severity == "low"]
        
        # Calculate Kevin's portability score
        total_issues = len(all_findings)
        critical_weight = len(critical) * 4
        high_weight = len(high) * 3
        medium_weight = len(medium) * 2
        low_weight = len(low) * 1
        
        total_weight = critical_weight + high_weight + medium_weight + low_weight
        
        # Score out of 5 (inverse of issue severity)
        if total_weight == 0:
            portability_score = 5.0
        else:
            portability_score = max(0.0, 5.0 - (total_weight / 15))
        
        # Runtime compatibility score
        compatible_runtimes = sum(1 for compatible in runtime_compatibility.values() if compatible)
        runtime_score = (compatible_runtimes / len(self.supported_runtimes)) * 5.0
        
        return {
            "kevin_portability_score": round(portability_score, 1),
            "runtime_compatibility_score": round(runtime_score, 1),
            "total_findings": total_issues,
            "severity_breakdown": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low)
            },
            "runtime_compatibility": runtime_compatibility,
            "compatible_runtimes": compatible_runtimes,
            "platform_independence": {
                "docker_free": not any("docker" in f.category for f in all_findings),
                "path_portable": not any("path" in f.category for f in all_findings),
                "config_portable": not any("config" in f.category for f in all_findings)
            },
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "description": f.description,
                    "file": f.file_path,
                    "line": f.line_number,
                    "evidence": f.evidence,
                    "platform_assumption": f.platform_assumption,
                    "suggested_abstraction": f.suggested_abstraction
                }
                for f in all_findings
            ],
            "kevin_recommendations": self._generate_kevin_recommendations(all_findings)
        }
    
    def _generate_kevin_recommendations(self, findings: List[PortabilityFinding]) -> List[str]:
        """🦙 Generate Kevin's portability recommendations"""
        recommendations = []
        
        if any("docker" in f.category for f in findings):
            recommendations.append("🔴 CRITICAL: Remove Docker-specific dependencies and implement runtime abstraction")
        
        if any("hardcoded" in f.category for f in findings):
            recommendations.append("🟡 HIGH: Replace hardcoded values with environment variables")
        
        if any("path" in f.category for f in findings):
            recommendations.append("🟡 HIGH: Use pathlib or os.path for cross-platform file operations")
        
        if any("network" in f.category for f in findings):
            recommendations.append("🟡 HIGH: Implement service discovery instead of hardcoded endpoints")
        
        recommendations.extend([
            "Implement runtime detection with graceful fallbacks",
            "Use 12-factor app configuration principles",
            "Add multi-architecture container support",
            "Create platform abstraction layer",
            "Test across multiple container runtimes",
            "Use cloud-native service discovery patterns"
        ])
        
        return recommendations[:10]  # Top 10 recommendations

def main():
    """🦙 Kevin's Portability Test Suite Entry Point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🦙 Kevin's Portability Analysis")
    parser.add_argument("target", help="File or directory to analyze")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--runtime-test", action="store_true", help="Test runtime compatibility")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    analyzer = KevinPortabilityAnalyzer()
    target_path = Path(args.target)
    
    print("🦙 Kevin the Portability Llama is analyzing your platform independence...")
    print("   \"Write once, run anywhere. Vendor lock-in is the enemy.\"")
    print()
    
    report = analyzer.generate_portability_report(target_path)
    
    # Print summary
    print(f"🦙 KEVIN'S PORTABILITY ASSESSMENT")
    print(f"Portability Score: {report['kevin_portability_score']}/5.0")
    print(f"Runtime Compatibility: {report['runtime_compatibility_score']}/5.0")
    print(f"Compatible Runtimes: {report['compatible_runtimes']}/{len(analyzer.supported_runtimes)}")
    print()
    
    if report['severity_breakdown']['critical'] > 0:
        print("🔴 CRITICAL PORTABILITY ISSUES - PLATFORM LOCK-IN DETECTED")
    elif report['severity_breakdown']['high'] > 0:
        print("🟡 HIGH PORTABILITY ISSUES - REDUCE PLATFORM DEPENDENCIES")
    else:
        print("✅ Good platform independence detected")
    
    print("\n🦙 Kevin's Top Recommendations:")
    for i, rec in enumerate(report['kevin_recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    if args.runtime_test:
        print("\n🔧 Runtime Compatibility Matrix:")
        for runtime, compatible in report['runtime_compatibility'].items():
            status = "✅" if compatible else "❌"
            print(f"  {status} {runtime}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📋 Full report saved to: {args.output}")

if __name__ == "__main__":
    main()