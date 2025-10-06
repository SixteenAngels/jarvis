from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from ..base import BaseAgent


ARTIFACTS_DIR = Path("/workspace/data/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


class ComputerEngineerAgent(BaseAgent):
    name: str = "computer_engineer"
    intents: List[str] = [
        "code",
        "compute",
        "software engineer",
        "computer engineer",
        "analyze code",
        "scaffold project",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("analyze code "):
            path_str = task.split(" ", 2)[2]
            p = Path(path_str)
            if not p.exists():
                return {"status": "error", "result": "path not found", "artifacts": []}
            report = self._analyze_code(p)
            return {"status": "ok", "result": report, "artifacts": []}

        if lower.startswith("scaffold project "):
            name = lower.split(" ", 2)[2]
            path = self._scaffold_project(name)
            return {"status": "ok", "result": f"project scaffolded at {path}", "artifacts": [{"type": "scaffold", "path": str(path)}]}

        return {"status": "error", "result": "Unknown computer engineering command", "artifacts": []}

    def _analyze_code(self, target: Path) -> str:
        files: List[Path] = []
        if target.is_dir():
            for p in target.rglob("*.py"):
                files.append(p)
        elif target.suffix == ".py":
            files.append(target)
        lines = 0
        for f in files:
            try:
                lines += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
            except Exception:
                pass
        return f"Analyzed {len(files)} files, {lines} total lines"

    def _scaffold_project(self, name: str) -> Path:
        root = ARTIFACTS_DIR / f"{name}_proj"
        pkg = root / name
        pkg.mkdir(parents=True, exist_ok=True)
        (root / "pyproject.toml").write_text(
            (
                "[project]\n"
                f"name = '{name}'\n"
                "version = '0.1.0'\n"
                "requires-python = '>=3.9'\n"
                "[build-system]\n"
                "requires = ['setuptools','wheel']\n"
                "build-backend = 'setuptools.build_meta'\n"
            ),
            encoding="utf-8",
        )
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "main.py").write_text("print('Hello from ComputerEngineerAgent scaffold')\n", encoding="utf-8")
        return root
