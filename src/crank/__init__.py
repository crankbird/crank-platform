"""
Crank platform package root.

Makes sure IDEs and tooling treat `crank.*` modules as a regular package
when the workspace adds `src/` to `PYTHONPATH`.

IMPORTANT: For imports to resolve correctly in VS Code/Pylance, these configs must be set:
- pyrightconfig.json: "extraPaths": ["src"] (global + tests execution environment)
- .vscode/settings.json: "python.analysis.extraPaths": ["${workspaceFolder}/src"]

If you see "Import 'crank.*' could not be resolved" errors, restart the language server
or verify the configs above. See docs/development/NEW_MACHINE_SETUP.md for details.
"""

# Submodules are importable via crank.capabilities, crank.typing_interfaces, etc.
# but not explicitly imported here to avoid potential circular dependencies during initialization
__all__: list[str] = []
