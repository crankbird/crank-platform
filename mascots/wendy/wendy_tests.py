#!/usr/bin/env python3
"""
🐰 Wendy's Zero-Trust Security Test Suite

Wendy the Zero-Trust Security Bunny's comprehensive security testing framework.
Includes Bobby Tables attack pattern detection and prevention validation.

Wendy's Philosophy:
"Never trust, always verify. Security is not a feature, it's a way of life.
Those who skimp on input sanitization deserve to meet Bobby Tables personally."
"""

import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    severity: str  # critical, high, medium, low
    category: str
    description: str
    file_path: str
    line_number: Optional[int]
    evidence: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    bobby_tables_risk: bool = False

class WendySecurityAnalyzer:
    """🐰 Wendy's Security Analysis Engine"""
    
    def __init__(self):
        self.findings: List[SecurityFinding] = []
        self.bobby_tables_patterns = self._load_bobby_tables_patterns()
        self.security_standards = self._load_security_standards()
    
    def _load_bobby_tables_patterns(self) -> Dict[str, List[str]]:
        """Load Bobby Tables attack patterns for detection"""
        return {
            "sql_injection": [
                r"SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*=\s*['\"]?\+",  # String concatenation in SQL
                r"\".*\"\s*\+\s*.*\+\s*\".*\"",  # String concatenation patterns
                r"'.*'\s*\+\s*.*\+\s*'.*'",
                r"execute\s*\(\s*['\"].*['\"].*\+",  # Dynamic SQL execution
                r"query\s*=\s*['\"].*['\"].*\+",  # Query string concatenation
                r"sql\s*=\s*['\"].*['\"].*\+",
            ],
            "command_injection": [
                r"os\.system\s*\(\s*.*\+",  # Command concatenation
                r"subprocess\..*\(\s*.*\+",
                r"exec\s*\(\s*.*\+",
                r"eval\s*\(\s*.*\+",
            ],
            "ldap_injection": [
                r"ldap.*search.*\+",
                r"filter\s*=\s*['\"].*['\"].*\+",
            ],
            "xpath_injection": [
                r"xpath.*\+",
                r"selectNodes.*\+",
            ]
        }
    
    def _load_security_standards(self) -> Dict:
        """Load Wendy's security compliance standards"""
        return {
            "owasp_top_10": [
                "A01_Broken_Access_Control",
                "A02_Cryptographic_Failures", 
                "A03_Injection",
                "A04_Insecure_Design",
                "A05_Security_Misconfiguration",
                "A06_Vulnerable_Components",
                "A07_Authentication_Failures",
                "A08_Software_Data_Integrity_Failures",
                "A09_Security_Logging_Failures",
                "A10_Server_Side_Request_Forgery"
            ],
            "nist_controls": [
                "AC-Access_Control",
                "AU-Audit_and_Accountability", 
                "AT-Awareness_and_Training",
                "CM-Configuration_Management",
                "CP-Contingency_Planning",
                "IA-Identification_and_Authentication",
                "IR-Incident_Response",
                "MA-Maintenance",
                "MP-Media_Protection",
                "PS-Personnel_Security",
                "PE-Physical_Protection",
                "PL-Planning", 
                "PM-Program_Management",
                "RA-Risk_Assessment",
                "CA-Security_Assessment",
                "SC-System_and_Communications_Protection",
                "SI-System_and_Information_Integrity",
                "SA-System_and_Services_Acquisition"
            ]
        }
    
    def analyze_file(self, file_path: Path) -> List[SecurityFinding]:
        """🐰 Wendy's comprehensive file security analysis"""
        findings = []
        
        if not file_path.exists():
            return findings
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Bobby Tables Pattern Detection
            findings.extend(self._detect_bobby_tables_patterns(file_path, content))
            
            # Input Validation Analysis
            findings.extend(self._analyze_input_validation(file_path, content))
            
            # Cryptographic Analysis
            findings.extend(self._analyze_cryptography(file_path, content))
            
            # Authentication & Authorization
            findings.extend(self._analyze_auth(file_path, content))
            
            # Secret Management
            findings.extend(self._analyze_secrets(file_path, content))
            
            # Network Security
            findings.extend(self._analyze_network_security(file_path, content))
            
        except Exception as e:
            logger.error(f"🐰 Wendy encountered error analyzing {file_path}: {e}")
            findings.append(SecurityFinding(
                severity="medium",
                category="analysis_error",
                description=f"Could not analyze file: {e}",
                file_path=str(file_path),
                line_number=None,
                evidence=str(e)
            ))
        
        return findings
    
    def _detect_bobby_tables_patterns(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """🐰 Detect Bobby Tables injection attack patterns"""
        findings = []
        lines = content.split('\n')
        
        for category, patterns in self.bobby_tables_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(SecurityFinding(
                            severity="critical",
                            category=f"bobby_tables_{category}",
                            description=f"Bobby Tables {category.replace('_', ' ').title()} pattern detected",
                            file_path=str(file_path),
                            line_number=line_num,
                            evidence=line.strip(),
                            cwe_id="CWE-89" if "sql" in category else "CWE-78",
                            owasp_category="A03_Injection",
                            bobby_tables_risk=True
                        ))
        
        return findings
    
    def _analyze_input_validation(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """🐰 Analyze input validation and sanitization"""
        findings = []
        lines = content.split('\n')
        
        # Look for missing input validation
        dangerous_functions = [
            r"request\.args\.get\s*\(\s*['\"].*['\"].*\)",
            r"request\.form\.get\s*\(\s*['\"].*['\"].*\)",
            r"request\.json\.get\s*\(\s*['\"].*['\"].*\)",
            r"input\s*\(\s*['\"].*['\"].*\)",
            r"raw_input\s*\(\s*['\"].*['\"].*\)"
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in dangerous_functions:
                if re.search(pattern, line):
                    # Check if validation follows
                    next_lines = lines[line_num:line_num+3]
                    validation_present = any(
                        re.search(r"validate|sanitize|escape|filter", next_line, re.IGNORECASE)
                        for next_line in next_lines
                    )
                    
                    if not validation_present:
                        findings.append(SecurityFinding(
                            severity="high",
                            category="missing_input_validation",
                            description="Input received without validation/sanitization",
                            file_path=str(file_path),
                            line_number=line_num,
                            evidence=line.strip(),
                            cwe_id="CWE-20",
                            owasp_category="A03_Injection"
                        ))
        
        return findings
    
    def _analyze_cryptography(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """🐰 Analyze cryptographic implementation"""
        findings = []
        lines = content.split('\n')
        
        # Weak cryptographic patterns
        weak_crypto = [
            (r"md5\s*\(", "MD5 is cryptographically broken", "CWE-327"),
            (r"sha1\s*\(", "SHA1 is cryptographically weak", "CWE-327"),
            (r"DES\s*\(", "DES encryption is broken", "CWE-327"),
            (r"RC4", "RC4 is cryptographically broken", "CWE-327"),
            (r"password\s*=\s*['\"].*['\"]", "Hardcoded password detected", "CWE-798")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, cwe in weak_crypto:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(SecurityFinding(
                        severity="high" if "broken" in description else "medium",
                        category="weak_cryptography",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        cwe_id=cwe,
                        owasp_category="A02_Cryptographic_Failures"
                    ))
        
        return findings
    
    def _analyze_auth(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """🐰 Analyze authentication and authorization"""
        findings = []
        lines = content.split('\n')
        
        # Authentication issues
        auth_issues = [
            (r"@app\.route.*methods.*POST.*", "POST endpoint without authentication", "CWE-306"),
            (r"session\[.*\]\s*=", "Session manipulation without validation", "CWE-613"),
            (r"jwt\.decode.*verify=False", "JWT verification disabled", "CWE-347")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, cwe in auth_issues:
                if re.search(pattern, line):
                    findings.append(SecurityFinding(
                        severity="high",
                        category="authentication_failure",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        cwe_id=cwe,
                        owasp_category="A07_Authentication_Failures"
                    ))
        
        return findings
    
    def _analyze_secrets(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """🐰 Analyze secret and credential management"""
        findings = []
        lines = content.split('\n')
        
        # Secret patterns
        secret_patterns = [
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
            (r"secret_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret key"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
            (r"[0-9a-f]{32}", "Potential MD5 hash/secret"),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in secret_patterns:
                if re.search(pattern, line):
                    findings.append(SecurityFinding(
                        severity="critical",
                        category="hardcoded_secrets",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence="[REDACTED - Secret detected]",
                        cwe_id="CWE-798",
                        owasp_category="A07_Authentication_Failures"
                    ))
        
        return findings
    
    def _analyze_network_security(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """🐰 Analyze network security configuration"""
        findings = []
        lines = content.split('\n')
        
        # Network security issues
        network_issues = [
            (r"requests\.get.*verify=False", "TLS verification disabled", "CWE-295"),
            (r"ssl_context\.check_hostname\s*=\s*False", "Hostname verification disabled", "CWE-295"),
            (r"urllib3\.disable_warnings", "SSL warnings disabled", "CWE-295"),
            (r"http://", "Unencrypted HTTP communication", "CWE-319")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, cwe in network_issues:
                if re.search(pattern, line):
                    findings.append(SecurityFinding(
                        severity="high",
                        category="network_security",
                        description=description,
                        file_path=str(file_path),
                        line_number=line_num,
                        evidence=line.strip(),
                        cwe_id=cwe,
                        owasp_category="A02_Cryptographic_Failures"
                    ))
        
        return findings
    
    def generate_security_report(self, target_path: Path) -> Dict:
        """🐰 Generate comprehensive security report"""
        all_findings = []
        
        if target_path.is_file():
            all_findings.extend(self.analyze_file(target_path))
        else:
            # Analyze all Python files in directory
            for py_file in target_path.rglob("*.py"):
                all_findings.extend(self.analyze_file(py_file))
        
        # Categorize findings
        critical = [f for f in all_findings if f.severity == "critical"]
        high = [f for f in all_findings if f.severity == "high"]
        medium = [f for f in all_findings if f.severity == "medium"]
        low = [f for f in all_findings if f.severity == "low"]
        
        bobby_tables_findings = [f for f in all_findings if f.bobby_tables_risk]
        
        # Calculate Wendy's security score
        total_issues = len(all_findings)
        critical_weight = len(critical) * 4
        high_weight = len(high) * 3
        medium_weight = len(medium) * 2
        low_weight = len(low) * 1
        
        total_weight = critical_weight + high_weight + medium_weight + low_weight
        
        # Score out of 5 (inverse of issue severity)
        if total_weight == 0:
            security_score = 5.0
        else:
            security_score = max(0.0, 5.0 - (total_weight / 10))
        
        return {
            "wendy_security_score": round(security_score, 1),
            "total_findings": total_issues,
            "severity_breakdown": {
                "critical": len(critical),
                "high": len(high), 
                "medium": len(medium),
                "low": len(low)
            },
            "bobby_tables_risks": len(bobby_tables_findings),
            "compliance_status": {
                "owasp_compliant": len(critical) == 0 and len(high) <= 2,
                "nist_aligned": len(critical) == 0,
                "bobby_tables_protected": len(bobby_tables_findings) == 0
            },
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "description": f.description,
                    "file": f.file_path,
                    "line": f.line_number,
                    "evidence": f.evidence,
                    "cwe": f.cwe_id,
                    "owasp": f.owasp_category,
                    "bobby_tables": f.bobby_tables_risk
                }
                for f in all_findings
            ],
            "wendy_recommendations": self._generate_wendy_recommendations(all_findings)
        }
    
    def _generate_wendy_recommendations(self, findings: List[SecurityFinding]) -> List[str]:
        """🐰 Generate Wendy's security recommendations"""
        recommendations = []
        
        if any(f.bobby_tables_risk for f in findings):
            recommendations.append("🔴 CRITICAL: Implement parameterized queries/prepared statements to prevent Bobby Tables attacks")
        
        if any(f.category == "hardcoded_secrets" for f in findings):
            recommendations.append("🔴 CRITICAL: Move all secrets to environment variables or secure vault")
        
        if any(f.category == "missing_input_validation" for f in findings):
            recommendations.append("🟡 HIGH: Implement comprehensive input validation and sanitization")
        
        if any(f.category == "weak_cryptography" for f in findings):
            recommendations.append("🟡 HIGH: Upgrade to strong cryptographic algorithms (AES-256, SHA-256+)")
        
        if any(f.category == "network_security" for f in findings):
            recommendations.append("🟡 HIGH: Enable TLS verification and use HTTPS for all communications")
        
        recommendations.extend([
            "Implement security logging and monitoring",
            "Add rate limiting to prevent brute force attacks", 
            "Conduct regular security audits",
            "Follow OWASP secure coding practices",
            "Implement zero-trust architecture principles"
        ])
        
        return recommendations[:10]  # Top 10 recommendations

def main():
    """🐰 Wendy's Security Test Suite Entry Point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🐰 Wendy's Zero-Trust Security Analysis")
    parser.add_argument("target", help="File or directory to analyze")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    analyzer = WendySecurityAnalyzer()
    target_path = Path(args.target)
    
    print("🐰 Wendy the Zero-Trust Security Bunny is analyzing your code...")
    print("   \"Never trust, always verify. Security is not negotiable.\"")
    print()
    
    report = analyzer.generate_security_report(target_path)
    
    # Print summary
    print(f"🐰 WENDY'S SECURITY ASSESSMENT")
    print(f"Security Score: {report['wendy_security_score']}/5.0")
    print(f"Total Issues: {report['total_findings']}")
    print(f"Bobby Tables Risks: {report['bobby_tables_risks']}")
    print()
    
    if report['severity_breakdown']['critical'] > 0:
        print("🔴 CRITICAL ISSUES DETECTED - IMMEDIATE ACTION REQUIRED")
    elif report['severity_breakdown']['high'] > 0:
        print("🟡 HIGH SEVERITY ISSUES - PRIORITIZE FIXES")
    else:
        print("✅ No critical security issues detected")
    
    print("\n🐰 Wendy's Top Recommendations:")
    for i, rec in enumerate(report['wendy_recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📋 Full report saved to: {args.output}")

if __name__ == "__main__":
    main()