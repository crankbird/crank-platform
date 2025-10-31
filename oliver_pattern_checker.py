#!/usr/bin/env python3
"""
🦅 Oliver's Evidence-Based Pattern Checker

This tool validates architectural decisions against established authorities.
Every flag includes citations to respected sources.

Usage:
    python oliver_pattern_checker.py [file_or_directory]
    python oliver_pattern_checker.py --check-all
    python oliver_pattern_checker.py --authority-sources
"""

import os
import re
import ast
import argparse
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PatternViolation:
    """Oliver's evidence-based pattern violation report"""
    file_path: str
    line_number: int
    violation_type: str
    description: str
    authority_sources: List[str]
    severity: str  # 'high', 'medium', 'low'
    remediation: str

class OliverPatternChecker:
    """Oliver's evidence-based architectural pattern validator"""
    
    def __init__(self):
        self.violations = []
        self.authority_sources = self._load_authority_sources()
    
    def _load_authority_sources(self) -> Dict[str, Dict]:
        """Oliver's authoritative source references"""
        return {
            "hardcoded_config": {
                "authorities": [
                    "12-Factor App - Config (12factor.net/config)",
                    "Kubernetes Best Practices (kubernetes.io/docs/concepts/configuration)",
                    "Docker Best Practices (docs.docker.com/develop/dev-best-practices)",
                    "AWS Well-Architected Framework - Configuration Management"
                ],
                "severity": "high",
                "description": "Configuration should be stored in environment variables, not hardcoded"
            },
            "god_object": {
                "authorities": [
                    "Martin, R.C. 'Clean Architecture' - Single Responsibility Principle",
                    "Fowler, M. 'Refactoring' - Large Class smell",
                    "Gang of Four 'Design Patterns' - Separation of concerns",
                    "Evans, E. 'Domain-Driven Design' - Bounded contexts"
                ],
                "severity": "high", 
                "description": "Classes should have single responsibility and focused cohesion"
            },
            "plaintext_secrets": {
                "authorities": [
                    "NIST SP 800-207 'Zero Trust Architecture'",
                    "OWASP Application Security Verification Standard",
                    "12-Factor App - Config separation",
                    "Google SRE 'Site Reliability Engineering' - Security patterns"
                ],
                "severity": "high",
                "description": "Secrets must never be stored in plaintext or hardcoded"
            },
            "shared_database": {
                "authorities": [
                    "Newman, S. 'Building Microservices' - Database per service",
                    "Fowler, M. 'Microservices' - Decentralized data management", 
                    "Evans, E. 'Domain-Driven Design' - Bounded context data",
                    "Richardson, C. 'Microservices Patterns' - Data consistency"
                ],
                "severity": "medium",
                "description": "Each service should own its data to maintain independence"
            },
            "synchronous_coupling": {
                "authorities": [
                    "Newman, S. 'Building Microservices' - Choreography vs Orchestration",
                    "Hohpe, G. 'Enterprise Integration Patterns' - Messaging patterns",
                    "Richardson, C. 'Microservices Patterns' - Communication patterns",
                    "Fowler, M. 'Patterns of Enterprise Application Architecture'"
                ],
                "severity": "medium", 
                "description": "Prefer asynchronous communication for loose coupling"
            },
            "no_health_checks": {
                "authorities": [
                    "Kubernetes Best Practices - Health checks",
                    "Google SRE 'Site Reliability Engineering' - Health monitoring",
                    "AWS Well-Architected Framework - Reliability pillar",
                    "12-Factor App - Disposability"
                ],
                "severity": "medium",
                "description": "Services should provide health check endpoints"
            },
            "root_container_user": {
                "authorities": [
                    "NIST Container Security Guide",
                    "Docker Security Best Practices",
                    "Kubernetes Pod Security Standards", 
                    "CIS Docker Benchmark"
                ],
                "severity": "high",
                "description": "Containers should run as non-root users for security"
            }
        }
    
    def check_hardcoded_configuration(self, file_path: str, content: str) -> List[PatternViolation]:
        """Check for hardcoded configuration - violates 12-Factor App principles"""
        violations = []
        lines = content.split('\n')
        
        # Common hardcoded patterns Oliver flags
        hardcoded_patterns = [
            (r'port\s*=\s*\d+', 'hardcoded port number'),
            (r'host\s*=\s*["\']localhost["\']', 'hardcoded host'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded API key'),
            (r'database_url\s*=\s*["\'][^"\']+["\']', 'hardcoded database URL'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in hardcoded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    authority = self.authority_sources["hardcoded_config"]
                    violations.append(PatternViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="Hardcoded Configuration",
                        description=f"{description}: {authority['description']}",
                        authority_sources=authority["authorities"],
                        severity=authority["severity"],
                        remediation="Use environment variables: os.getenv('PORT', '8000')"
                    ))
        
        return violations
    
    def check_god_objects(self, file_path: str, content: str) -> List[PatternViolation]:
        """Check for God Objects - violates Single Responsibility Principle"""
        violations = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Count methods (excluding __init__, __str__, etc.)
                    method_count = sum(1 for n in node.body 
                                     if isinstance(n, ast.FunctionDef) 
                                     and not n.name.startswith('__'))
                    
                    # Oliver's threshold: >15 methods suggests God Object
                    if method_count > 15:
                        authority = self.authority_sources["god_object"]
                        violations.append(PatternViolation(
                            file_path=file_path,
                            line_number=node.lineno,
                            violation_type="God Object",
                            description=f"Class '{node.name}' has {method_count} methods. {authority['description']}",
                            authority_sources=authority["authorities"],
                            severity=authority["severity"],
                            remediation="Split into smaller, focused classes with single responsibilities"
                        ))
        
        except SyntaxError:
            # Not a Python file or syntax error
            pass
        
        return violations
    
    def check_plaintext_secrets(self, file_path: str, content: str) -> List[PatternViolation]:
        """Check for plaintext secrets - violates Zero Trust principles"""
        violations = []
        lines = content.split('\n')
        
        # Patterns that suggest plaintext secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{6,}["\']', 'hardcoded password'),
            (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'hardcoded secret'),
            (r'token\s*=\s*["\'][A-Za-z0-9]{20,}["\']', 'hardcoded token'),
            (r'api_key\s*=\s*["\'][A-Za-z0-9]{15,}["\']', 'hardcoded API key'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    authority = self.authority_sources["plaintext_secrets"]
                    violations.append(PatternViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="Plaintext Secrets",
                        description=f"{description}: {authority['description']}",
                        authority_sources=authority["authorities"],
                        severity=authority["severity"],
                        remediation="Use environment variables and secret management systems"
                    ))
        
        return violations
    
    def check_dockerfile_antipatterns(self, file_path: str, content: str) -> List[PatternViolation]:
        """Check Dockerfile for security and efficiency anti-patterns"""
        violations = []
        
        if not file_path.lower().endswith('dockerfile') and 'dockerfile' not in file_path.lower():
            return violations
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for root user (security anti-pattern)
            if re.match(r'USER\s+root\s*$', line, re.IGNORECASE):
                authority = self.authority_sources["root_container_user"]
                violations.append(PatternViolation(
                    file_path=file_path,
                    line_number=line_num,
                    violation_type="Root Container User",
                    description=f"Running as root user: {authority['description']}",
                    authority_sources=authority["authorities"],
                    severity=authority["severity"],
                    remediation="Create and use non-root user: RUN adduser --disabled-password myuser && USER myuser"
                ))
        
        return violations
    
    def check_file(self, file_path: str) -> List[PatternViolation]:
        """Oliver's comprehensive file analysis"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Run all pattern checks
            violations.extend(self.check_hardcoded_configuration(file_path, content))
            violations.extend(self.check_god_objects(file_path, content))
            violations.extend(self.check_plaintext_secrets(file_path, content))
            violations.extend(self.check_dockerfile_antipatterns(file_path, content))
            
        except Exception as e:
            print(f"🦅 Oliver couldn't analyze {file_path}: {e}")
        
        return violations
    
    def check_directory(self, directory_path: str) -> List[PatternViolation]:
        """Oliver's recursive directory analysis"""
        violations = []
        
        # File types Oliver examines
        file_extensions = {'.py', '.dockerfile', '.yml', '.yaml', '.js', '.ts', '.go', '.java'}
        
        for root, dirs, files in os.walk(directory_path):
            # Skip common directories Oliver ignores
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv'}]
            
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                # Check files with relevant extensions or special names
                if ext.lower() in file_extensions or 'dockerfile' in file.lower():
                    violations.extend(self.check_file(file_path))
        
        return violations
    
    def generate_report(self, violations: List[PatternViolation]) -> str:
        """Oliver's evidence-based violation report"""
        if not violations:
            return "🦅 Oliver's Assessment: No anti-patterns detected! Architecture is clean! ✨"
        
        report = ["🦅 Oliver's Anti-Pattern Analysis Report", "=" * 50, ""]
        
        # Group by severity
        high_severity = [v for v in violations if v.severity == 'high']
        medium_severity = [v for v in violations if v.severity == 'medium']
        low_severity = [v for v in violations if v.severity == 'low']
        
        if high_severity:
            report.extend(["🚨 HIGH SEVERITY - Immediate Action Required:", ""])
            for violation in high_severity:
                report.extend(self._format_violation(violation))
        
        if medium_severity:
            report.extend(["⚠️  MEDIUM SEVERITY - Plan Remediation:", ""])
            for violation in medium_severity:
                report.extend(self._format_violation(violation))
        
        if low_severity:
            report.extend(["📋 LOW SEVERITY - Monitor and Improve:", ""])
            for violation in low_severity:
                report.extend(self._format_violation(violation))
        
        # Summary
        report.extend([
            "",
            f"📊 Oliver's Summary:",
            f"   Total violations: {len(violations)}",
            f"   High severity: {len(high_severity)}",
            f"   Medium severity: {len(medium_severity)}",
            f"   Low severity: {len(low_severity)}",
            "",
            "🦅 Oliver's Recommendation: Address high severity items first!",
            ""
        ])
        
        return "\n".join(report)
    
    def _format_violation(self, violation: PatternViolation) -> List[str]:
        """Format individual violation with citations"""
        lines = [
            f"📍 {violation.file_path}:{violation.line_number}",
            f"   Pattern: {violation.violation_type}",
            f"   Issue: {violation.description}",
            f"   Fix: {violation.remediation}",
            "   Authority Sources:"
        ]
        
        for source in violation.authority_sources:
            lines.append(f"     • {source}")
        
        lines.append("")
        return lines

def main():
    parser = argparse.ArgumentParser(description="🦅 Oliver's Evidence-Based Pattern Checker")
    parser.add_argument('path', nargs='?', default='.', help='File or directory to check')
    parser.add_argument('--check-all', action='store_true', help='Check entire current directory')
    parser.add_argument('--authority-sources', action='store_true', help='Show Oliver\'s authority sources')
    
    args = parser.parse_args()
    
    oliver = OliverPatternChecker()
    
    if args.authority_sources:
        print("🦅 Oliver's Authority Sources:")
        print("=" * 30)
        for pattern, info in oliver.authority_sources.items():
            print(f"\n{pattern.upper()}:")
            for source in info['authorities']:
                print(f"  • {source}")
        return
    
    target_path = args.path if not args.check_all else '.'
    
    print(f"🦅 Oliver analyzing: {os.path.abspath(target_path)}")
    print("Checking against established architectural authorities...")
    print()
    
    if os.path.isfile(target_path):
        violations = oliver.check_file(target_path)
    else:
        violations = oliver.check_directory(target_path)
    
    report = oliver.generate_report(violations)
    print(report)
    
    # Exit code for CI/CD integration
    return len([v for v in violations if v.severity == 'high'])

if __name__ == "__main__":
    exit(main())