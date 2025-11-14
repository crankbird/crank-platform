#!/usr/bin/env python3
"""
Zettel Integration Script
Merges Codex systematic analysis with Sonnet thematic synthesis.

This version is path-agnostic, deduplicates by slug, and preserves original
front matter while layering standardized metadata for downstream tooling.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional

import yaml

# Add src to path for philosophical analyzer import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from unified_knowledge_base.philosophical_analyzer import enhance_frontmatter_with_analysis
    PHILOSOPHICAL_ANALYSIS_AVAILABLE = True
except ImportError:
    PHILOSOPHICAL_ANALYSIS_AVAILABLE = False


@dataclass
class SourceRecord:
    source: str
    path: str


class ZettelIntegrator:
    """Handle ingestion, normalization, and deduplication of zettels."""

    def __init__(
        self,
        project_root: Path,
        codex_dir: Path,
        sonnet_dir: Path,
        output_dir: Path,
        verbose: bool = False,
    ) -> None:
        self.project_root = project_root
        self.codex_dir = codex_dir
        self.sonnet_dir = sonnet_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.zettels: Dict[str, Dict[str, Any]] = {}

    def integrate_collections(self) -> None:
        """Main integration pipeline."""
        self._process_directory(self.codex_dir / "content" / "zettels", "codex")
        self._process_directory(self.sonnet_dir / "01-zettels", "sonnet")
        for master_file in self.sonnet_dir.glob("MASTER-ZETTEL*.md"):
            self._process_file(master_file, "master")
        self._flush_zettels()

    def _process_directory(self, source_dir: Path, source_type: str) -> None:
        if not source_dir.exists():
            return
        for md_file in source_dir.rglob("*.md"):
            self._process_file(md_file, source_type)

    def _process_file(self, source_file: Path, source_type: str) -> None:
        if self.verbose:
            print(f"📝 Processing {source_file} ({source_type})")

        content = source_file.read_text(encoding="utf-8")
        frontmatter, body = self.standardize_frontmatter(content, source_file)
        slug = frontmatter["slug"]
        
        # Use relative path from project root if possible, otherwise use name
        try:
            relative_path = str(source_file.relative_to(self.project_root))
        except ValueError:
            # Source file is outside project root, use relative to parent dir
            relative_path = f"../{source_file.parent.name}/{source_file.name}"
        
        source_info = SourceRecord(
            source=source_type,
            path=relative_path,
        )

        record = self.zettels.get(slug)
        if record:
            record["frontmatter"] = self._merge_frontmatter(
                record["frontmatter"], frontmatter
            )
            record["body"] = self._prefer_body(record["body"], body)
            record["sources"].append(source_info)
        else:
            self.zettels[slug] = {
                "frontmatter": frontmatter,
                "body": body,
                "sources": [source_info],
            }

    def _flush_zettels(self) -> None:
        for slug, payload in self.zettels.items():
            fm = payload["frontmatter"].copy()
            fm["source_files"] = [
                {"source": record.source, "path": record.path}
                for record in payload["sources"]
            ]
            fm["source_collections"] = sorted(
                {record.source for record in payload["sources"]}
            )
            output_path = self.output_dir / f"{slug}.md"
            output_path.write_text(
                f"---\n{yaml.safe_dump(fm, sort_keys=False)}---\n{payload['body']}",
                encoding="utf-8",
            )

    # --------------------------------------------------------------------- #
    # Frontmatter helpers
    # --------------------------------------------------------------------- #
    def standardize_frontmatter(
        self, content: str, source_path: Path
    ) -> tuple[Dict[str, Any], str]:
        """Standardize frontmatter for Jekyll/Obsidian compatibility."""
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if frontmatter_match:
            existing_fm = yaml.safe_load(frontmatter_match.group(1)) or {}
            body = frontmatter_match.group(2)
        else:
            existing_fm = {}
            body = content

        fm = dict(existing_fm)  # shallow copy so we don't mutate originals
        title = fm.get("title") or self._extract_title(body)

        fm.setdefault("id", self._generate_id(source_path))
        fm.setdefault("title", title)
        fm.setdefault("slug", self._generate_slug(title))
        fm.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        fm["tags"] = self._standardize_tags(fm.get("tags", []))
        fm.setdefault("type", self._determine_type(source_path, body))
        fm.setdefault("schema", "v1.2")
        
        # Use sophisticated philosophical analysis if available, fallback to simple
        if PHILOSOPHICAL_ANALYSIS_AVAILABLE:
            fm = enhance_frontmatter_with_analysis(fm, title, body)
        else:
            # Fallback to basic philosophical markers
            fm["philosophical_markers"] = self._merge_philosophical_markers(
                fm.get("philosophical_markers"), body
            )
        
        fm.setdefault("related_zettels", fm.get("related", []))
        fm.setdefault("parent_themes", fm.get("parent_themes", []))
        fm.setdefault("business_applications", fm.get("business_applications", []))
        fm.setdefault("jekyll_ready", True)
        fm.setdefault("content_type", self._determine_content_type(source_path, body))
        fm.setdefault("target_audience", self._determine_audience(source_path, body))
        fm.setdefault("gherkin_source", self._contains_gherkins(body))
        fm.setdefault("implementation_priority", self._assess_priority(source_path, body))

        return fm, body

    def _merge_frontmatter(
        self, existing: Dict[str, Any], incoming: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = dict(existing)
        for key, value in incoming.items():
            if key not in merged or merged[key] in (None, "", [], {}):
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key] = self._merge_lists(merged[key], value)
            elif isinstance(value, MutableMapping) and isinstance(
                merged[key], MutableMapping
            ):
                merged[key] = self._merge_frontmatter(merged[key], value)
        return merged

    def _merge_lists(self, primary: List[Any], secondary: List[Any]) -> List[Any]:
        combined = list(primary)
        seen = {self._freeze(item) for item in primary}
        for item in secondary:
            frozen = self._freeze(item)
            if frozen not in seen:
                combined.append(item)
                seen.add(frozen)
        return combined

    @staticmethod
    def _freeze(item: Any) -> Any:
        if isinstance(item, dict):
            return tuple(sorted((k, ZettelIntegrator._freeze(v)) for k, v in item.items()))
        if isinstance(item, list):
            return tuple(ZettelIntegrator._freeze(v) for v in item)
        return item

    def _merge_philosophical_markers(
        self, existing: Optional[Dict[str, bool]], body: str
    ) -> Dict[str, bool]:
        markers = existing.copy() if isinstance(existing, dict) else {}
        defaults = {
            "situated_intelligence": False,
            "temporal_dynamics": False,
            "identity_plurality": False,
            "distributed_agency": False,
            "data_gravity": False,
        }
        defaults.update(markers)
        body_lower = body.lower()
        checks = {
            "situated_intelligence": ["situated", "context", "local", "edge"],
            "temporal_dynamics": ["time", "temporal", "uneven", "future", "emergence"],
            "identity_plurality": ["identity", "persona", "multiple", "plurality"],
            "distributed_agency": ["distributed", "agent", "network", "coordination"],
            "data_gravity": ["metadata", "data", "meaning", "semantic"],
        }
        for key, keywords in checks.items():
            if defaults.get(key):
                continue
            defaults[key] = any(term in body_lower for term in keywords)
        return defaults

    def _generate_id(self, path: Path) -> str:
        return path.stem.lower().replace(" ", "-").replace("_", "-")

    def _extract_title(self, body: str) -> str:
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        return title_match.group(1).strip() if title_match else "Untitled"

    def _generate_slug(self, title: str) -> str:
        return re.sub(r"[^\w\s-]", "", title.lower()).replace(" ", "-")

    def _standardize_tags(self, existing_tags: Any) -> List[str]:
        if isinstance(existing_tags, str):
            return [existing_tags]
        if isinstance(existing_tags, list):
            return [str(tag) for tag in existing_tags]
        return []

    def _determine_type(self, path: Path, body: str) -> str:
        if "persona" in str(path).lower():
            return "persona"
        if "gherkin" in body.lower() or "feature:" in body.lower():
            return "gherkin"
        if "master-zettel" in str(path).lower():
            return "synthesis"
        if "business" in str(path).lower():
            return "business-strategy"
        return "zettel"

    def _determine_content_type(self, path: Path, body: str) -> str:
        if "business" in str(path).lower():
            return "marketing"
        if "gherkin" in body.lower():
            return "documentation"
        if "master-zettel" in str(path).lower():
            return "philosophy"
        return "blog-post"

    def _determine_audience(self, path: Path, body: str) -> List[str]:
        if "technical" in str(path).lower() or "gherkin" in body.lower():
            return ["developers"]
        if "business" in str(path).lower() or "executive" in body.lower():
            return ["executives"]
        if "research" in str(path).lower():
            return ["researchers"]
        return ["developers", "executives"]

    def _contains_gherkins(self, body: str) -> bool:
        lowered = body.lower()
        return "gherkin" in lowered or "feature:" in lowered or "scenario:" in lowered

    def _assess_priority(self, path: Path, body: str) -> str:
        path_lower = str(path).lower()
        body_lower = body.lower()
        if "master-zettel" in path_lower:
            return "high"
        if "gherkin" in body_lower or "business" in path_lower:
            return "high"
        if "persona" in path_lower:
            return "medium"
        return "low"

    @staticmethod
    def _prefer_body(current: str, new_body: str) -> str:
        if not current.strip():
            return new_body
        if len(new_body.strip()) > len(current.strip()):
            return new_body
        return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Integrate Codex + Sonnet zettels into a unified knowledge base."
    )
    default_root = Path(__file__).resolve().parents[1]
    default_codex = default_root.parent / "codex-second-pass"
    default_sonnet = default_root.parent / "sonnet-curated-workspace"

    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_root,
        help="Path to unified-knowledge-base project root",
    )
    parser.add_argument(
        "--codex-dir",
        type=Path,
        default=default_codex,
        help="Path to Codex export directory",
    )
    parser.add_argument(
        "--sonnet-dir",
        type=Path,
        default=default_sonnet,
        help="Path to Sonnet export directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_root / "zettels",
        help="Destination directory for merged zettels",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print progress for each file"
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    integrator = ZettelIntegrator(
        project_root=args.project_root.resolve(),
        codex_dir=args.codex_dir.resolve(),
        sonnet_dir=args.sonnet_dir.resolve(),
        output_dir=args.output_dir.resolve(),
        verbose=args.verbose,
    )
    integrator.integrate_collections()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
