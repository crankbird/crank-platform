#!/usr/bin/env python3
import ast
import sys
from pathlib import Path


def transform_signature(fn):
    changed = False
    args = fn.args
    # Pair last N args with defaults
    n = len(args.defaults)
    if n == 0:
        return False
    tail_params = args.args[-n:]
    new_defaults = []
    for param, default in zip(tail_params, list(args.defaults)):
        if isinstance(default, ast.Call) and getattr(default.func, "id", "") == "Depends":
            if param.annotation is None:
                # cannot transform safely without an annotation
                new_defaults.append(default)
                continue
            ann = ast.Subscript(
                value=ast.Name(id="Annotated", ctx=ast.Load()),
                slice=ast.Tuple(elts=[param.annotation, default], ctx=ast.Load()),
                ctx=ast.Load(),
            )
            param.annotation = ann
            changed = True
        else:
            new_defaults.append(default)
    if changed:
        args.defaults = new_defaults
    return changed


class Rewriter(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.changed = False

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if transform_signature(node):
            self.changed = True
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        if transform_signature(node):
            self.changed = True
        return node


def ensure_typing_annotated(src: str) -> str:
    # Add "from typing import Annotated" if missing
    if "Annotated" in src and "from typing import Annotated" in src:
        return src
    lines = src.splitlines()
    for i, line in enumerate(lines[:20]):
        if line.startswith("from typing import"):
            if "Annotated" in line:
                return src
            lines[i] = line.rstrip() + ", Annotated"
            return "\n".join(lines)
    return "from typing import Annotated\n" + src


def process_file(p: Path):
    text = p.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    rw = Rewriter()
    rw.visit(tree)
    if not rw.changed:
        return False
    new_src = ast.unparse(tree) if hasattr(ast, "unparse") else text
    new_src = ensure_typing_annotated(new_src)
    p.write_text(new_src, encoding="utf-8")
    print(f"[fix-fastapi-di] updated {p}")
    return True


def main():
    targets = sys.argv[1:] or ["src", "services", "app", "routers"]
    for base in targets:
        b = Path(base)
        if not b.exists():
            continue
        for py in b.rglob("*.py"):
            process_file(py)


if __name__ == "__main__":
    main()
