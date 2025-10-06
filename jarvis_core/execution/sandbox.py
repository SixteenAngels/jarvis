from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class SandboxResult:
    status: str
    returncode: int
    stdout: str
    stderr: str


class Sandbox:
    """Very conservative command sandbox for local execution.

    - Whitelist commands explicitly
    - No shell=True
    - Timeouts
    - Environment sanitization
    """

    def __init__(self, allowed_commands: Optional[List[str]] = None, default_timeout: int = 10) -> None:
        self.allowed_commands = set(allowed_commands or [
            'echo', 'ls', 'pwd', 'cat', 'python3', 'pip', 'uname'
        ])
        self.default_timeout = default_timeout

    def run(self, command_line: str, timeout: Optional[int] = None, cwd: Optional[str] = None) -> SandboxResult:
        if not command_line or not command_line.strip():
            return SandboxResult(status='error', returncode=1, stdout='', stderr='Empty command')

        parts = shlex.split(command_line)
        executable = parts[0]
        if os.path.basename(executable) not in self.allowed_commands:
            return SandboxResult(status='error', returncode=1, stdout='', stderr=f'Command not allowed: {executable}')

        # Build environment: minimal pass-through
        env: Dict[str, str] = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'LANG', 'LC_ALL'}}

        try:
            proc = subprocess.run(
                parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                timeout=timeout or self.default_timeout,
                check=False,
                text=True,
            )
        except subprocess.TimeoutExpired as e:
            return SandboxResult(status='timeout', returncode=124, stdout=e.stdout or '', stderr=e.stderr or 'timeout')
        except Exception as e:  # pragma: no cover - rare system errors
            return SandboxResult(status='error', returncode=1, stdout='', stderr=str(e))

        status = 'ok' if proc.returncode == 0 else 'error'
        return SandboxResult(status=status, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
