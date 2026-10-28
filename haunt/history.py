"""Read the user's shell history locally for the 'seance' command."""
from __future__ import annotations

import os
import re
from pathlib import Path

SECRET_RE = re.compile(r"(pass(word|wd)?|token|secret|api[_-]?key|bearer|authorization|aws_|private)",
                       re.I)


def history_candidates() -> list:
    home = Path.home()
    paths = [home / ".bash_history", home / ".zsh_history"]
    appdata = os.environ.get("APPDATA")
    if appdata:  # Windows PowerShell
        paths.append(Path(appdata) / "Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt")
    return paths


def load_history(limit: int = 25, path: str | None = None) -> list:
    """Return the last `limit` unique commands (oldest first), dropping secret-looking lines."""
    files = [Path(path)] if path else [p for p in history_candidates() if p.exists()]
    if not files:
        return []
    raw = files[0].read_text(errors="ignore").splitlines()
    cmds, seen = [], set()
    for line in reversed(raw):
        line = re.sub(r"^: \d+:\d+;", "", line).strip()  # zsh extended-history prefix
        if not line or SECRET_RE.search(line) or line in seen:
            continue
        seen.add(line)
        cmds.append(line)
        if len(cmds) >= limit:
            break
    return list(reversed(cmds))
