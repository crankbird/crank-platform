"""Philosophical Analyzer Worker Service

This worker provides philosophical content analysis capabilities using
the canonical schema for DNA marker detection and coherence scoring.

The service evolved from the experimental philosophical analyzer
(archived in archive/2025-11-14-golden-repository/) and integrates
with the crank worker runtime infrastructure.
"""

import asyncio
import logging
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from crank.capabilities.schema import PHILOSOPHICAL_ANALYSIS, CapabilityDefinition
from crank.capabilities.semantic_config import load_schema
from crank.worker_runtime.base import WorkerApplication

logger = logging.getLogger(__name__)


class PhilosophicalAnalyzer:
    """
    Core philosophical analysis engine.

    Implements the philosophical DNA marker detection patterns
    using the semantic configuration from the crank platform.
    """

    def __init__(self):
        self.schema = load_schema()
        logger.info(f"Initialized with {len(self.schema.marker_codes)} DNA markers")

    def analyze_text(self, text: str, analysis_type: str = "full_analysis", context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Analyze text for philosophical DNA markers and authenticity.

        Args:
            text: Content to analyze
            analysis_type: Type of analysis to perform
            context: Optional context information

        Returns:
            Analysis results with DNA markers, authenticity score, and summary
        """
        if len(text.strip()) < 50:
            raise ValueError("Text too short for meaningful analysis")

        context = context or {}

        # Perform DNA marker analysis
        dna_markers = self._analyze_dna_markers(text)

        # Calculate authenticity score
        authenticity_score = self._calculate_authenticity(text, dna_markers)

        # Generate analysis summary
        summary = self._generate_summary(text, dna_markers, authenticity_score)

        # Detect patterns
        patterns = self._detect_patterns(text)

        result: dict[str, Any] = {
            "dna_markers": dna_markers,
            "authenticity_score": authenticity_score,
            "analysis_summary": summary,
            "confidence": self._calculate_confidence(text, dna_markers),
        }

        if analysis_type == "full_analysis":
            result["detected_patterns"] = patterns
            result["readiness_thresholds"] = dict(self.schema.readiness_thresholds)

        return result

    def _analyze_dna_markers(self, text: str) -> dict[str, float]:
        """Analyze text for primary philosophical DNA markers."""
        markers = {}
        text_lower = text.lower()

        for code, marker in self.schema.primary_markers.items():
            score = 0.0

            # Keyword matching with weighting
            keyword_matches = sum(1 for keyword in marker.keywords if keyword.lower() in text_lower)
            if keyword_matches > 0:
                score += (keyword_matches / len(marker.keywords)) * marker.weight * 0.4

            # Pattern matching (simplified - would use regex in full implementation)
            pattern_matches = sum(1 for pattern in marker.patterns
                                if self._simple_pattern_match(pattern, text_lower))
            if pattern_matches > 0:
                score += (pattern_matches / len(marker.patterns)) * marker.weight * 0.6

            # Normalize to 0-1 range
            markers[code] = min(score, 1.0)

        return markers

    def _simple_pattern_match(self, pattern: str, text: str) -> bool:
        """Simple pattern matching (placeholder for full regex implementation)."""
        # Remove regex syntax for basic substring matching
        cleaned_pattern = pattern.replace("\\w*", "").replace("[-\\s]", " ").replace("?", "")
        return cleaned_pattern.lower() in text

    def _calculate_authenticity(self, text: str, dna_markers: dict[str, float]) -> float:
        """Calculate authenticity vs. performed thinking score."""
        # Simple heuristic: higher marker diversity indicates more authentic thinking
        active_markers = sum(1 for score in dna_markers.values() if score > 0.2)
        max_markers = len(dna_markers)

        # Bonus for text length (more room for authentic development)
        length_bonus = min(len(text) / 2000.0, 0.3)

        # Combination score
        diversity_score = active_markers / max_markers if max_markers > 0 else 0

        return min(diversity_score + length_bonus, 1.0)

    def _generate_summary(self, text: str, dna_markers: dict[str, float], authenticity: float) -> str:
        """Generate human-readable analysis summary."""
        top_markers = sorted(dna_markers.items(), key=lambda x: x[1], reverse=True)[:2]

        if not top_markers or top_markers[0][1] < 0.1:
            return "Limited philosophical content detected. Consider adding more conceptual depth."

        marker_names = []
        for code, score in top_markers:
            if score > 0.2:
                marker = self.schema.get_marker(code)
                if marker:
                    marker_names.append(marker.name)

        summary = f"Primary philosophical themes: {', '.join(marker_names)}. "

        if authenticity > 0.6:
            summary += "High authenticity - appears to be genuine conceptual exploration."
        elif authenticity > 0.3:
            summary += "Moderate authenticity - some genuine insights mixed with standard content."
        else:
            summary += "Lower authenticity - may be more performative or template-based."

        return summary

    def _detect_patterns(self, text: str) -> list[str]:
        """Detect specific philosophical patterns in the text."""
        patterns = []
        text_lower = text.lower()

        # Check for key philosophical thinking patterns
        if "context" in text_lower and ("different" in text_lower or "depends" in text_lower):
            patterns.append("Context-dependent reasoning")

        if "future" in text_lower and ("uneven" in text_lower or "emerging" in text_lower):
            patterns.append("Temporal complexity awareness")

        if "identity" in text_lower and ("multiple" in text_lower or "different" in text_lower):
            patterns.append("Identity multiplicity recognition")

        if "agent" in text_lower or "autonomous" in text_lower or "distributed" in text_lower:
            patterns.append("Distributed agency thinking")

        return patterns

    def _calculate_confidence(self, text: str, dna_markers: dict[str, float]) -> float:
        """Calculate confidence in the analysis."""
        # Confidence based on text length and marker strength
        length_factor = min(len(text) / 1000.0, 1.0)  # Longer text = higher confidence
        marker_strength = max(dna_markers.values()) if dna_markers else 0

        return (length_factor * 0.4 + marker_strength * 0.6)


class PhilosophicalAnalyzerWorker(WorkerApplication):
    """Worker service providing philosophical analysis capabilities."""

    def __init__(self, worker_id: str | None = None, service_name: str | None = None, https_port: int = 8500):
        super().__init__(
            worker_id=worker_id,
            service_name=service_name or "philosophical-analyzer",
            https_port=https_port,
        )
        self.analyzer = PhilosophicalAnalyzer()

    def setup_routes(self) -> None:
        """Register HTTP routes for the philosophical analysis service."""

        @self.app.post("/analyze")
        async def analyze_endpoint(request: dict[str, Any]) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
            """Main analysis endpoint matching the capability contract."""
            try:
                # Validate required fields
                text = request.get("text")
                if not text:
                    raise HTTPException(status_code=400, detail="Missing required field: text")

                analysis_type = request.get("analysis_type", "full_analysis")
                context = request.get("context")

                # Perform analysis
                result = self.analyzer.analyze_text(text, analysis_type, context)

                return JSONResponse(content=result)

            except ValueError as e:
                if "too short" in str(e).lower():
                    raise HTTPException(status_code=400, detail="TEXT_TOO_SHORT") from e
                raise HTTPException(status_code=400, detail="INVALID_CONTEXT") from e
            except Exception as e:
                logger.exception("Analysis failed")
                raise HTTPException(status_code=500, detail="ANALYSIS_FAILED") from e

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return the capabilities this worker provides."""
        return [PHILOSOPHICAL_ANALYSIS]

    async def on_startup(self) -> None:
        """Worker startup initialization."""
        logger.info("Philosophical analyzer worker starting up")
        await super().on_startup()
        logger.info("Philosophical analyzer ready to process requests")

    async def on_shutdown(self) -> None:
        """Worker shutdown cleanup."""
        logger.info("Philosophical analyzer worker shutting down")
        await super().on_shutdown()


async def main():
    """Entry point for running the philosophical analyzer worker."""
    import uvicorn

    worker = PhilosophicalAnalyzerWorker()

    # Run the FastAPI application
    config = uvicorn.Config(
        worker.app,
        host="0.0.0.0",
        port=8001,  # Use different port from controller
        log_level="info",
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - just verify imports and basic functionality
        worker = PhilosophicalAnalyzerWorker()
        print(f"Worker capabilities: {[cap.name for cap in worker.get_capabilities()]}")

        # Test analysis
        test_result = worker.analyzer.analyze_text(
            "This is a test of context-dependent intelligence that emerges from distributed agents working in different temporal contexts."
        )
        print(f"Test analysis result: {test_result['analysis_summary']}")
    else:
        asyncio.run(main())
