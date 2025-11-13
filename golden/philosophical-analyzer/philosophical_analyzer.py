"""
Philosophical content analyzer using canonical schema.
Provides sophisticated theme detection and coherence scoring.
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

from philosophical_schema import PHILOSOPHICAL_SCHEMA


@dataclass
class PhilosophicalAnalysis:
    """Results of philosophical content analysis."""
    primary_markers: Dict[str, float]
    secondary_themes: Dict[str, float] 
    coherence_score: float
    detected_patterns: List[str]
    suggested_personas: List[str]
    connections: List[str]


class PhilosophicalAnalyzer:
    """Advanced philosophical content analysis using canonical schema."""
    
    def __init__(self):
        self.schema = PHILOSOPHICAL_SCHEMA
        self.readiness_thresholds = self.schema.get("readiness_thresholds", {
            "publication_ready": 3.5,
            "cross_reference_eligible": 2.8,
            "cluster_priority": 2.5,
            "integration_minimum": 2.0
        })
        self.linking_thresholds = {
            "semantic_similarity": 0.75,
            "theme_overlap": 0.6,
            "cross_reference_boost": 1.2,
            "temporal_decay": 0.95
        }
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self.compiled_patterns = {}
        
        for marker_id, config in self.schema["primary_markers"].items():
            patterns = config.get("patterns", [])
            if patterns:
                combined = "|".join(f"({pattern})" for pattern in patterns)
                self.compiled_patterns[marker_id] = re.compile(
                    combined, re.IGNORECASE | re.MULTILINE
                )
    
    def analyze_content(self, title: str, body: str, existing_tags: List[str] = None) -> PhilosophicalAnalysis:
        """
        Analyze content for philosophical themes and coherence.
        
        Args:
            title: Document title
            body: Document body text
            existing_tags: Any existing tag classifications
            
        Returns:
            Comprehensive philosophical analysis
        """
        content = f"{title}\n\n{body}".lower()
        existing_tags = existing_tags or []
        
        # Analyze primary philosophical markers
        primary_markers = self._analyze_primary_markers(content)
        
        # Analyze secondary themes
        secondary_themes = self._analyze_secondary_themes(content, existing_tags)
        
        # Calculate overall coherence
        coherence_score = self._calculate_coherence(primary_markers, secondary_themes)
        
        # Detect specific patterns that triggered classification
        detected_patterns = self._get_detected_patterns(content)
        
        # Suggest target personas based on philosophical alignment
        suggested_personas = self._suggest_personas(primary_markers)
        
        # Generate connection suggestions
        connections = self._suggest_connections(primary_markers, secondary_themes)
        
        return PhilosophicalAnalysis(
            primary_markers=primary_markers,
            secondary_themes=secondary_themes,
            coherence_score=coherence_score,
            detected_patterns=detected_patterns,
            suggested_personas=suggested_personas,
            connections=connections
        )
    
    def _analyze_primary_markers(self, content: str) -> Dict[str, float]:
        """Analyze content for core philosophical principles."""
        markers = {}
        
        for marker_id, config in self.schema["primary_markers"].items():
            score = 0.0
            
            # Keyword matching with frequency weighting
            keywords = config["keywords"]
            keyword_matches = sum(content.count(keyword.lower()) for keyword in keywords)
            keyword_score = min(keyword_matches * 0.2, 2.0)  # Max 2.0 from keywords
            
            # Pattern matching with higher weight
            pattern_score = 0.0
            if marker_id in self.compiled_patterns:
                pattern_matches = len(self.compiled_patterns[marker_id].findall(content))
                pattern_score = min(pattern_matches * 0.8, 3.0)  # Max 3.0 from patterns
            
            # Combined score with marker weight
            total_score = (keyword_score + pattern_score) * config["weight"]
            markers[marker_id] = min(total_score, 5.0)  # Cap at 5.0
        
        return markers
    
    def _analyze_secondary_themes(self, content: str, existing_tags: List[str]) -> Dict[str, float]:
        """Analyze content for secondary thematic elements."""
        themes = {}
        
        for theme_id, config in self.schema["secondary_themes"].items():
            score = 0.0
            
            # Check existing tags first
            theme_name = config["name"].lower().replace("-", " ")
            if any(theme_name in tag.lower() for tag in existing_tags):
                score += 2.0
            
            # Keyword analysis
            keywords = config["keywords"] 
            keyword_matches = sum(content.count(keyword.lower()) for keyword in keywords)
            keyword_score = min(keyword_matches * 0.3, 3.0)
            
            # Apply theme weight
            total_score = (score + keyword_score) * config["weight"]
            themes[theme_id] = min(total_score, 5.0)
        
        return themes
    
    def _calculate_coherence(self, primary_markers: Dict[str, float], secondary_themes: Dict[str, float]) -> float:
        """Calculate overall philosophical coherence score."""
        # Primary markers are most important for coherence
        primary_max = max(primary_markers.values()) if primary_markers else 0.0
        primary_avg = sum(primary_markers.values()) / len(primary_markers) if primary_markers else 0.0
        primary_score = (primary_max * 0.7) + (primary_avg * 0.3)
        
        # Secondary themes provide supporting evidence
        secondary_score = max(secondary_themes.values()) if secondary_themes else 0.0
        
        # Weighted combination
        coherence = (primary_score * 0.8) + (secondary_score * 0.2)
        
        return round(min(coherence, 5.0), 1)
    
    def _get_detected_patterns(self, content: str) -> List[str]:
        """Return specific patterns that were detected in content."""
        patterns = []
        
        for marker_id, pattern_regex in self.compiled_patterns.items():
            matches = pattern_regex.findall(content)
            if matches:
                marker_name = self.schema["primary_markers"][marker_id]["name"]
                # Flatten tuple matches from grouped regex
                flat_matches = []
                for match in matches:
                    if isinstance(match, tuple):
                        flat_matches.extend([m for m in match if m])
                    else:
                        flat_matches.append(match)
                
                if flat_matches:
                    patterns.append(f"{marker_name}: {', '.join(flat_matches[:3])}")
        
        return patterns
    
    def _suggest_personas(self, primary_markers: Dict[str, float]) -> List[str]:
        """Suggest target personas based on philosophical markers."""
        persona_scores = {}
        
        for marker_id, score in primary_markers.items():
            if score >= 2.0:  # Only consider significant markers
                personas = self.schema["persona_mappings"].get(marker_id, [])
                for persona in personas:
                    persona_scores[persona] = persona_scores.get(persona, 0) + score
        
        # Return personas sorted by relevance
        sorted_personas = sorted(persona_scores.items(), key=lambda x: x[1], reverse=True)
        return [persona for persona, score in sorted_personas if score >= 2.0]
    
    def _suggest_connections(self, primary_markers: Dict[str, float], secondary_themes: Dict[str, float]) -> List[str]:
        """Generate connection suggestions based on philosophical analysis."""
        connections = []
        
        # Connections based on primary markers
        strong_markers = [mid for mid, score in primary_markers.items() if score >= 3.0]
        for marker_id in strong_markers:
            marker_name = self.schema["primary_markers"][marker_id]["name"]
            connections.append(f"Strong {marker_name} content - link to related philosophical zettels")
        
        # Connections based on secondary themes
        strong_themes = [tid for tid, score in secondary_themes.items() if score >= 3.0] 
        for theme_id in strong_themes:
            theme_name = self.schema["secondary_themes"][theme_id]["name"]
            connections.append(f"High {theme_name} relevance - consider cross-reference to application examples")
        
        return connections

    def assess_readiness(self, analysis: PhilosophicalAnalysis) -> dict[str, bool]:
        """Assess content readiness for various publication/integration stages."""
        coherence = analysis.coherence_score
        
        return {
            "publication_ready": coherence >= self.readiness_thresholds["publication_ready"],
            "cross_reference_eligible": coherence >= self.readiness_thresholds["cross_reference_eligible"],
            "cluster_priority": coherence >= self.readiness_thresholds["cluster_priority"],
            "integration_minimum": coherence >= self.readiness_thresholds["integration_minimum"]
        }

    def calculate_linking_score(
        self,
        content_a: PhilosophicalAnalysis,
        content_b: PhilosophicalAnalysis,
        temporal_distance_days: float = 0
    ) -> float:
        """Calculate sophisticated linking score between two pieces of content."""
        
        # Theme overlap scoring
        themes_a = set(content_a.primary_markers.keys()) | set(content_a.secondary_themes.keys())
        themes_b = set(content_b.primary_markers.keys()) | set(content_b.secondary_themes.keys())
        theme_overlap = len(themes_a & themes_b) / len(themes_a | themes_b) if themes_a | themes_b else 0
        
        # Coherence boost for high-quality content
        coherence_factor = min(content_a.coherence_score, content_b.coherence_score) / 5.0
        
        # Temporal decay (recent content links more easily)
        temporal_factor = self.linking_thresholds["temporal_decay"] ** temporal_distance_days
        
        # Cross-reference boost for complementary themes
        cross_ref_boost = 1.0
        if theme_overlap > self.linking_thresholds["theme_overlap"]:
            cross_ref_boost = self.linking_thresholds["cross_reference_boost"]
        
        base_score = theme_overlap * coherence_factor * temporal_factor * cross_ref_boost
        
        return min(base_score, 1.0)


def enhance_frontmatter_with_analysis(
    existing_frontmatter: Dict[str, Any], 
    title: str, 
    body: str
) -> Dict[str, Any]:
    """
    Enhance existing frontmatter with sophisticated philosophical analysis.
    
    Args:
        existing_frontmatter: Current frontmatter dict
        title: Document title
        body: Document content
        
    Returns:
        Enhanced frontmatter with philosophical_analysis section
    """
    analyzer = PhilosophicalAnalyzer()
    existing_tags = existing_frontmatter.get("tags", [])
    
    analysis = analyzer.analyze_content(title, body, existing_tags)
    
    # Add philosophical analysis to frontmatter
    enhanced = existing_frontmatter.copy()
    enhanced["philosophical_analysis"] = {
        "primary_markers": {
            mid: round(score, 1) for mid, score in analysis.primary_markers.items() 
            if score >= 1.0  # Only include meaningful scores
        },
        "secondary_themes": {
            tid: round(score, 1) for tid, score in analysis.secondary_themes.items()
            if score >= 1.0
        },
        "coherence_score": analysis.coherence_score,
        "detected_patterns": analysis.detected_patterns[:5],  # Top 5 patterns
        "suggested_personas": analysis.suggested_personas,
        "connection_suggestions": analysis.connections[:3]  # Top 3 connections
    }
    
    # Add derived metadata for content pipeline
    enhanced["publication_readiness"] = _assess_publication_readiness(existing_frontmatter, analysis)
    enhanced["target_audiences"] = analysis.suggested_personas
    
    return enhanced


def _assess_publication_readiness(frontmatter: Dict[str, Any], analysis: PhilosophicalAnalysis) -> float:
    """Assess how ready content is for publication based on metadata completeness."""
    score = 0.0
    
    # Check required fields
    if frontmatter.get("title"): score += 1.0
    if frontmatter.get("summary"): score += 1.0  
    if frontmatter.get("attribution"): score += 1.0
    
    # Check philosophical coherence
    if analysis.coherence_score >= 3.0: score += 1.0
    if analysis.coherence_score >= 4.0: score += 1.0
    
    # Check for call-to-action or next steps
    body_lower = frontmatter.get("body", "").lower()
    if any(phrase in body_lower for phrase in ["next steps", "action items", "implementation", "try this"]):
        score += 1.0
    
    return round(min(score / 6.0 * 5.0, 5.0), 1)  # Scale to 5.0 max