#!/usr/bin/env python3
"""
Gherkin Extraction Script
Extracts behavioral specifications from zettels with full traceability
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

class GherkinExtractor:
    def __init__(self, unified_dir="/Users/richardmartin/Documents/AA-raw-ideas/unified-knowledge-base"):
        self.unified_dir = Path(unified_dir)
        self.zettels_dir = self.unified_dir / "zettels"
        self.gherkins_dir = self.unified_dir / "gherkins"
        
    def extract_all_gherkins(self):
        """Extract all gherkin scenarios with traceability links"""
        print("🥒 Extracting gherkins from zettel collection...")
        
        features = {}
        
        # Process all markdown files
        for md_file in self.zettels_dir.glob("*.md"):
            gherkins = self._extract_from_file(md_file)
            for feature_name, scenarios in gherkins.items():
                if feature_name not in features:
                    features[feature_name] = {
                        'scenarios': [],
                        'source_files': [],
                        'related_zettels': [],
                        'themes': []
                    }
                features[feature_name]['scenarios'].extend(scenarios)
                features[feature_name]['source_files'].append(str(md_file))
                
        # Generate feature files
        for feature_name, feature_data in features.items():
            self._generate_feature_file(feature_name, feature_data)
            
        print(f"✅ Generated {len(features)} feature files with traceability")
        
    def _extract_from_file(self, md_file: Path) -> Dict:
        """Extract gherkins from a single markdown file"""
        content = md_file.read_text(encoding='utf-8')
        
        # Extract frontmatter for metadata
        frontmatter = self._extract_frontmatter(content)
        
        features = {}
        
        # Find gherkin blocks
        gherkin_blocks = re.findall(
            r'```gherkin\n(.*?)\n```', 
            content, 
            re.DOTALL | re.MULTILINE
        )
        
        for block in gherkin_blocks:
            feature_match = re.search(r'Feature:\s*(.+)', block)
            if feature_match:
                feature_name = feature_match.group(1).strip()
                scenarios = self._parse_scenarios(block)
                
                if feature_name not in features:
                    features[feature_name] = []
                    
                for scenario in scenarios:
                    scenario['source_file'] = str(md_file)
                    scenario['source_tags'] = frontmatter.get('tags', [])
                    scenario['philosophical_markers'] = frontmatter.get('philosophical_markers', {})
                    
                features[feature_name].extend(scenarios)
                
        return features
        
    def _extract_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from content"""
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            try:
                return yaml.safe_load(frontmatter_match.group(1))
            except yaml.YAMLError:
                return {}
        return {}
        
    def _parse_scenarios(self, gherkin_block: str) -> List[Dict]:
        """Parse scenarios from gherkin block"""
        scenarios = []
        
        # Split by Scenario: markers
        scenario_sections = re.split(r'Scenario:\s*', gherkin_block)[1:]  # Skip first split (before first scenario)
        
        for section in scenario_sections:
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            scenario_name = lines[0].strip()
            steps = []
            
            for line in lines[1:]:
                line = line.strip()
                if line and not line.startswith('#'):
                    steps.append(line)
                    
            scenarios.append({
                'name': scenario_name,
                'steps': steps
            })
            
        return scenarios
        
    def _generate_feature_file(self, feature_name: str, feature_data: Dict):
        """Generate a complete feature file with traceability"""
        
        # Clean feature name for filename
        filename = re.sub(r'[^\w\s-]', '', feature_name.lower()).replace(' ', '-')
        feature_file = self.gherkins_dir / f"{filename}.feature"
        
        # Collect unique source information
        source_files = list(set(feature_data['source_files']))
        all_tags = set()
        all_themes = set()
        
        for scenario in feature_data['scenarios']:
            all_tags.update(scenario.get('source_tags', []))
            
        # Generate feature file content
        content = f"""# Feature: {feature_name}
# 
# Traceability Information:
# Source Files: {', '.join(source_files)}
# Related Tags: {', '.join(sorted(all_tags))}
# Generated: {self._get_timestamp()}
#
# This feature file is auto-generated from zettel analysis.
# To update: modify source zettels and re-run extraction.

Feature: {feature_name}

"""
        
        # Add all scenarios
        for i, scenario in enumerate(feature_data['scenarios']):
            if i > 0:
                content += "\n"
                
            content += f"  # Source: {scenario['source_file']}\n"
            content += f"  Scenario: {scenario['name']}\n"
            
            for step in scenario['steps']:
                content += f"    {step}\n"
                
        # Write feature file
        feature_file.write_text(content, encoding='utf-8')
        
        # Generate traceability metadata
        metadata_file = self.gherkins_dir / f"{filename}.metadata.yaml"
        metadata = {
            'feature_name': feature_name,
            'source_files': source_files,
            'tags': sorted(all_tags),
            'scenario_count': len(feature_data['scenarios']),
            'philosophical_alignment': self._assess_philosophical_alignment(feature_data['scenarios']),
            'implementation_priority': self._assess_implementation_priority(feature_data['scenarios']),
            'generated_at': self._get_timestamp()
        }
        
        metadata_file.write_text(yaml.dump(metadata, default_flow_style=False), encoding='utf-8')
        
    def _assess_philosophical_alignment(self, scenarios: List[Dict]) -> Dict:
        """Assess which philosophical principles the scenarios embody"""
        alignment = {
            'situated_intelligence': 0,
            'temporal_dynamics': 0,
            'identity_plurality': 0,
            'distributed_agency': 0,
            'data_gravity': 0
        }
        
        total_scenarios = len(scenarios)
        if total_scenarios == 0:
            return alignment
            
        for scenario in scenarios:
            markers = scenario.get('philosophical_markers', {})
            for principle, present in markers.items():
                if present:
                    alignment[principle] += 1
                    
        # Convert to percentages
        for principle in alignment:
            alignment[principle] = round(alignment[principle] / total_scenarios * 100, 1)
            
        return alignment
        
    def _assess_implementation_priority(self, scenarios: List[Dict]) -> str:
        """Assess implementation priority based on scenario content"""
        high_priority_keywords = ['security', 'economic', 'payment', 'sla', 'core', 'critical']
        medium_priority_keywords = ['persona', 'context', 'adaptation']
        
        high_count = 0
        medium_count = 0
        
        for scenario in scenarios:
            scenario_text = f"{scenario['name']} {' '.join(scenario['steps'])}".lower()
            
            if any(keyword in scenario_text for keyword in high_priority_keywords):
                high_count += 1
            elif any(keyword in scenario_text for keyword in medium_priority_keywords):
                medium_count += 1
                
        if high_count > len(scenarios) * 0.3:
            return 'high'
        elif medium_count > len(scenarios) * 0.3:
            return 'medium'
        return 'low'
        
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata"""
        from datetime import datetime
        return datetime.now().isoformat()

    def generate_dev_repo_package(self):
        """Generate a package ready for import into development repo"""
        
        package_dir = self.unified_dir / "dev-repo-package"
        package_dir.mkdir(exist_ok=True)
        
        # Copy all feature files
        import shutil
        
        for feature_file in self.gherkins_dir.glob("*.feature"):
            shutil.copy2(feature_file, package_dir)
            
        # Generate import script
        import_script = package_dir / "import-to-dev-repo.sh"
        import_script.write_text("""#!/bin/bash
# Import script for Crank Platform development repo
#
# Usage: ./import-to-dev-repo.sh [target-repo-path]

TARGET_REPO=${1:-"../crank-platform"}
FEATURES_DIR="$TARGET_REPO/tests/behavioral-specs"

echo "🥒 Importing gherkin specifications..."

# Create target directory
mkdir -p "$FEATURES_DIR"

# Copy feature files
for feature in *.feature; do
    echo "  📋 Importing $feature"
    cp "$feature" "$FEATURES_DIR/"
done

echo "✅ Import complete! Features available in $FEATURES_DIR"
echo ""
echo "Next steps:"
echo "1. cd $TARGET_REPO"
echo "2. Run your gherkin test suite to validate current implementation"
echo "3. Use failing tests as implementation guide"
""", encoding='utf-8')
        
        import_script.chmod(0o755)
        
        print(f"📦 Development package ready at {package_dir}")

if __name__ == "__main__":
    extractor = GherkinExtractor()
    extractor.extract_all_gherkins()
    extractor.generate_dev_repo_package()