from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from .base import BaseAgent


class SoftwareAgent(BaseAgent):
    name: str = "software"
    intents: List[str] = [
        "scaffold",
        "cli",
        "project",
        "software",
        "init",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("scaffold cli"):
            # format: scaffold cli <name>
            name = lower.replace("scaffold cli", "").strip() or "my_cli"
            path = self._scaffold_cli(name)
            return {"status": "ok", "result": f"CLI scaffolded at {path}", "artifacts": [{"type": "scaffold", "path": str(path)}]}
        return {"status": "error", "result": "Unknown software command", "artifacts": []}

    def _scaffold_cli(self, name: str) -> Path:
        target = Path("/workspace/data/artifacts") / f"{name}_cli"
        pkg = target / name
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "__main__.py").write_text(
            (
                "import argparse\n"
                "def main():\n"
                "    parser = argparse.ArgumentParser(prog='" + name + "')\n"
                "    parser.add_argument('--name', default='world')\n"
                "    args = parser.parse_args()\n"
                "    print(f'Hello, {args.name}!')\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            encoding="utf-8",
        )
        (target / "pyproject.toml").write_text(
            (
                "[project]\n"
                f"name = '{name}'\n"
                "version = '0.1.0'\n"
                "requires-python = '>=3.9'\n"
                "[project.scripts]\n"
                f"{name} = '{name}.__main__:main'\n"
            ),
            encoding="utf-8",
        )
        return target
