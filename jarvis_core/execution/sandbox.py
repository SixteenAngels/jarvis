from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
import tarfile
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

try:  # Resource limits (POSIX)
    import resource  # type: ignore
except Exception:  # pragma: no cover
    resource = None  # type: ignore


@dataclass
class SandboxResult:
    status: str
    returncode: int
    stdout: str
    stderr: str


class Sandbox:
    """Production-oriented sandbox with quotas and rollback artifacts.

    Features:
    - Explicit command allowlist
    - No shell=True
    - Timeouts and POSIX resource limits (if available)
    - Per-task ephemeral workspace with rollback archive (stdout/stderr)
    - Sanitized environment
    """

    def __init__(self, allowed_commands: Optional[List[str]] = None, default_timeout: int = 10,
                 cpu_seconds: int = 5, memory_mb: int = 256) -> None:
        self.allowed_commands = set(allowed_commands or [
            'echo', 'ls', 'pwd', 'cat', 'python3', 'pip', 'uname'
        ])
        self.default_timeout = default_timeout
        self.cpu_seconds = cpu_seconds
        self.memory_mb = memory_mb

    def _set_limits(self) -> None:
        if resource is None:
            return
        # CPU time
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_seconds, self.cpu_seconds))
        except Exception:
            pass
        # Address space (approximate memory)
        try:
            mem_bytes = self.memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except Exception:
            pass

    def run(self, command_line: str, timeout: Optional[int] = None, cwd: Optional[str] = None) -> SandboxResult:
        if not command_line or not command_line.strip():
            return SandboxResult(status='error', returncode=1, stdout='', stderr='Empty command')

        parts = shlex.split(command_line)
        executable = parts[0]
        if os.path.basename(executable) not in self.allowed_commands:
            return SandboxResult(status='error', returncode=1, stdout='', stderr=f'Command not allowed: {executable}')

        # Build environment: minimal pass-through
        env: Dict[str, str] = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'LANG', 'LC_ALL'}}
        # Create per-task workspace
        workdir = tempfile.mkdtemp(prefix="sandbox_")
        if cwd:
            workdir = cwd
        stdout_path = os.path.join(workdir, "stdout.txt")
        stderr_path = os.path.join(workdir, "stderr.txt")
        try:
            with open(stdout_path, 'w') as out, open(stderr_path, 'w') as err:
                proc = subprocess.run(
                    parts,
                    stdout=out,
                    stderr=err,
                    cwd=workdir,
                    env=env,
                    timeout=timeout or self.default_timeout,
                    check=False,
                    text=True,
                    preexec_fn=self._set_limits if resource is not None else None,
                )
            # Read outputs
            with open(stdout_path, 'r') as f:
                stdout_data = f.read()
            with open(stderr_path, 'r') as f:
                stderr_data = f.read()
        except subprocess.TimeoutExpired as e:
            stdout_data = ''
            stderr_data = 'timeout'
            proc = type('proc', (), {'returncode': 124})()  # minimal object
        except Exception as e:  # pragma: no cover - rare system errors
            return SandboxResult(status='error', returncode=1, stdout='', stderr=str(e))

        # Create rollback archive
        try:
            archive = os.path.join(workdir, 'artifact.tar.gz')
            with tarfile.open(archive, 'w:gz') as tar:
                for name in (stdout_path, stderr_path):
                    if os.path.exists(name):
                        tar.add(name, arcname=os.path.basename(name))
        except Exception:
            pass

        status = 'ok' if getattr(proc, 'returncode', 1) == 0 else 'error'
        return SandboxResult(status=status, returncode=getattr(proc, 'returncode', 1), stdout=stdout_data, stderr=stderr_data)
