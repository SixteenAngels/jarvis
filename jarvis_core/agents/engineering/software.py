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

        if lower.startswith("lint code "):
            path_str = task.split(" ", 2)[2]
            p = Path(path_str)
            if not p.exists():
                return {"status": "error", "result": "path not found", "artifacts": []}
            issues = self._lint_code(p)
            summary = f"{len(issues)} issues\n" + "\n".join(issues[:200])
            return {"status": "ok", "result": summary, "artifacts": [{"type": "lint", "count": len(issues)}]}

        if lower.startswith("deps report "):
            path_str = task.split(" ", 2)[2]
            p = Path(path_str)
            if not p.exists():
                return {"status": "error", "result": "path not found", "artifacts": []}
            report = self._deps_report(p)
            return {"status": "ok", "result": report, "artifacts": []}

        if lower.startswith("scaffold project "):
            name = lower.split(" ", 2)[2]
            path = self._scaffold_project(name)
            return {"status": "ok", "result": f"project scaffolded at {path}", "artifacts": [{"type": "scaffold", "path": str(path)}]}

        return {"status": "error", "result": "Unknown computer engineering command", "artifacts": []}

    def _analyze_code(self, target: Path) -> str:
        files = self._collect_py_files(target)
        total_lines = 0
        largest: List[tuple[int, Path]] = []
        import_edges: List[str] = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            line_count = len(content.splitlines())
            total_lines += line_count
            largest.append((line_count, f))
            imports = self._extract_imports(content)
            for mod in imports:
                import_edges.append(f"{f.stem} -> {mod}")
        largest.sort(reverse=True)
        largest_str = ", ".join([f"{p.name}:{n}" for n, p in largest[:5]])
        return (
            f"Analyzed {len(files)} files, {total_lines} total lines\n"
            f"Top files: {largest_str}\n"
            f"Imports: {min(len(import_edges), 50)} edges"
        )

    def _lint_code(self, target: Path) -> List[str]:
        files = self._collect_py_files(target)
        issues: List[str] = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    issues.append(f"{f}:{i}: line too long ({len(line)} > 120)")
                if line.endswith(" "):
                    issues.append(f"{f}:{i}: trailing whitespace")
                if "\t" in line:
                    issues.append(f"{f}:{i}: tab character used; prefer spaces")
            if not content.endswith("\n"):
                issues.append(f"{f}: missing newline at EOF")
        return issues

    def _deps_report(self, target: Path) -> str:
        reqs: List[str] = []
        pyproj: List[str] = []
        req_path = target / "requirements.txt"
        if req_path.exists():
            try:
                reqs = [l.strip() for l in req_path.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]
            except Exception:
                pass
        pyproj_path = target / "pyproject.toml"
        if pyproj_path.exists():
            try:
                for l in pyproj_path.read_text().splitlines():
                    if l.strip().startswith("dependencies") or ("==" in l and "project" not in l.lower()):
                        pyproj.append(l.strip())
            except Exception:
                pass
        return (
            f"requirements: {len(reqs)} packages\n" + "\n".join(reqs[:50]) + "\n" +
            f"pyproject lines: {len(pyproj)}\n" + "\n".join(pyproj[:50])
        )

    def _collect_py_files(self, target: Path) -> List[Path]:
        files: List[Path] = []
        if target.is_dir():
            for p in target.rglob("*.py"):
                files.append(p)
        elif target.suffix == ".py":
            files.append(target)
        return files

    def _extract_imports(self, content: str) -> List[str]:
        mods: List[str] = []
        for line in content.splitlines():
            ls = line.strip()
            if ls.startswith("import "):
                parts = ls.split()
                if len(parts) >= 2:
                    mods.append(parts[1].split(".")[0])
            elif ls.startswith("from "):
                parts = ls.split()
                if len(parts) >= 2:
                    mods.append(parts[1].split(".")[0])
        return mods

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
        (root / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        return root
