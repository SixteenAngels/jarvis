from __future__ import annotations

from pathlib import Path

from jarvis_core.core.router import Router
from jarvis_core.agents.engineering.software import ComputerEngineerAgent


def test_computer_engineer_lint_and_deps(tmp_path: Path) -> None:
    # Create a small project
    proj = tmp_path / "p"
    pkg = proj / "p"
    pkg.mkdir(parents=True)
    (proj / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    (proj / "pyproject.toml").write_text("[project]\nname='p'\nversion='0.1.0'\n", encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "m.py").write_text("import os\nprint('x')\t\n" + "#"*130 + "\n", encoding="utf-8")

    r = Router(agents=[ComputerEngineerAgent()])
    lint = r.route(f"lint code {proj}")
    assert lint["status"] == "ok" and "issues" in lint["result"]

    deps = r.route(f"deps report {proj}")
    assert deps["status"] == "ok" and "requirements:" in deps["result"]
