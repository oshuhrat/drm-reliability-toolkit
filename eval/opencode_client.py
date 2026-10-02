"""Thin wrapper around the `opencode run` CLI, used by run_cases.py and judge.py.

OpenCode has no system-prompt flag, so a system prompt is sent as an
<instructions> block at the top of the single user message. OpenCode also adds
its own agent prompt; that is identical for every method, so it does not
differentiate them, but results describe "model + OpenCode agent", not the bare
model. Each call runs in an empty temporary directory so the agent has no
project files to read.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def resolve_binary(configured: str | None = None) -> str:
    """Prefer the real opencode.exe: .cmd/.ps1 shims mangle multi-line arguments."""
    if configured:
        return configured
    found = shutil.which("opencode")
    if not found:
        raise SystemExit("`opencode` not found on PATH; set opencode_bin in the config")
    shim_dir = Path(found).resolve().parent
    exe = shim_dir / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
    return str(exe) if exe.exists() else found


def compose_prompt(system: str | None, user: str) -> str:
    if not system:
        return user
    return f"<instructions>\n{system.strip()}\n</instructions>\n\n{user}"


def clean_output(raw: str) -> str:
    text = _ANSI.sub("", raw).replace("\r\n", "\n")
    lines = text.split("\n")
    # drop leading blank lines and the "> <agent> · <model>" header
    while lines and (not lines[0].strip() or lines[0].startswith("> ")):
        lines.pop(0)
    return "\n".join(lines).strip() + "\n"


def run_opencode(model: str, prompt: str, *, binary: str | None = None, timeout: int = 600) -> dict:
    """One call, no retries. Raises RuntimeError on failure or an error banner."""
    exe = resolve_binary(binary)
    with tempfile.TemporaryDirectory(prefix="drm-eval-") as workdir:
        proc = subprocess.run(
            [exe, "run", "-m", model, "--dir", workdir, prompt],
            capture_output=True,
            timeout=timeout,
            cwd=workdir,
            env={**os.environ, "NO_COLOR": "1"},
        )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    text = clean_output(stdout)
    if proc.returncode != 0 or text.lstrip().startswith("Error:"):
        raise RuntimeError(f"opencode exit {proc.returncode}: {(text or _ANSI.sub('', stderr))[:400].strip()}")
    return {"text": text, "response_model": model, "stop_reason": "end_turn", "usage": None}
