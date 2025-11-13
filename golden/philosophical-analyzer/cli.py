#!/usr/bin/env python3
"""
Command-line interface for unified knowledge base tools.
"""

import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def add_project_root_to_path() -> None:
    """Add project root to Python path for script imports."""
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))


@click.group()
@click.version_option()
def cli() -> None:
    """Unified Knowledge Base integration tools."""
    pass


@cli.command("integrate-zettels")
@click.option("--codex-dir", default=None, help="Path to Codex export directory")
@click.option("--sonnet-dir", default=None, help="Path to Sonnet export directory")
@click.option("--output-dir", default=None, help="Destination for merged zettels")
@click.option("--verbose", is_flag=True, help="Verbose output")
def integrate_zettels_main(
    codex_dir: Optional[str],
    sonnet_dir: Optional[str],
    output_dir: Optional[str],
    verbose: bool,
) -> None:
    """Integrate and standardize zettel collections."""
    add_project_root_to_path()
    
    try:
        from integrate_zettels import main as integrate_main
        
        argv: List[str] = []
        if codex_dir:
            argv.extend(["--codex-dir", codex_dir])
        if sonnet_dir:
            argv.extend(["--sonnet-dir", sonnet_dir])
        if output_dir:
            argv.extend(["--output-dir", output_dir])
        if verbose:
            argv.append("--verbose")
        integrate_main(argv)
            
    except ImportError:
        console.print("[red]Error: Could not import integrate-zettels script[/red]")
        sys.exit(1)


@cli.command("extract-gherkins")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--output", default="./gherkins", help="Output directory")
def extract_gherkins_main(dry_run: bool, verbose: bool, output: str) -> None:
    """Extract gherkin scenarios from zettels."""
    add_project_root_to_path()
    
    try:
        from extract_gherkins import main as extract_main
        
        old_argv = sys.argv.copy()
        sys.argv = ["extract-gherkins"]
        if dry_run:
            sys.argv.append("--dry-run")
        if verbose:
            sys.argv.append("--verbose")
        sys.argv.extend(["--output", output])
        
        try:
            extract_main()
        finally:
            sys.argv = old_argv
            
    except ImportError:
        console.print("[red]Error: Could not import extract-gherkins script[/red]")
        sys.exit(1)


@cli.command("test-infrastructure")
def test_infrastructure_main() -> None:
    """Test infrastructure setup and validation."""
    add_project_root_to_path()
    
    try:
        from test_infrastructure import main as test_main
        exit_code = test_main()
        sys.exit(exit_code)
        
    except ImportError:
        console.print("[red]Error: Could not import test-infrastructure script[/red]")
        sys.exit(1)


@cli.command("setup")
@click.option("--obsidian", is_flag=True, help="Open in Obsidian after setup")
def setup_main(obsidian: bool) -> None:
    """Set up the unified knowledge base infrastructure."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Test infrastructure
        task1 = progress.add_task("Testing infrastructure...", total=None)
        test_infrastructure_main()
        progress.remove_task(task1)
        
        # Integrate zettels
        task2 = progress.add_task("Integrating zettel collections...", total=None)
        integrate_zettels_main(None, None, None, False)
        progress.remove_task(task2)

        # Extract gherkins
        task3 = progress.add_task("Extracting gherkin scenarios...", total=None)
        extract_gherkins_main(False, False, "./gherkins")
        progress.remove_task(task3)
    
    console.print("✅ [green]Setup complete![/green]")
    console.print()
    console.print("Next steps:")
    console.print("• Open this directory in Obsidian as a vault")
    console.print("• Explore the knowledge graph starting from the Master Zettel")
    console.print("• Import gherkins from ./gherkins/ into your development repo")
    
    if obsidian:
        console.print()
        console.print("Opening in Obsidian...")
        import subprocess
        subprocess.run(["open", "-a", "Obsidian", "."])


if __name__ == "__main__":
    cli()
