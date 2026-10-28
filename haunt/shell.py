"""The haunted shell: a thin REPL that runs your commands normally, then lets the ghost react."""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from .ghost import Ghost
from .omens import find_omens
from .personas import PERSONAS

PURPLE = "\x1b[35m"
DIM = "\x1b[2m"
ITAL = "\x1b[3m"
RESET = "\x1b[0m"

BANNER = f"""{PURPLE}
   .-.
  (o o)   haunt {DIM}- a terminal that whispers back{RESET}{PURPLE}
  | O \\   type commands as usual. type {RESET}:help{PURPLE} for ghost controls.
   \\   \\
    `~~~'
{RESET}"""

HELP = """  :persona NAME   switch ghost (sysadmin, victorian, poltergeist, ofrenda)
  :chance 0.4     how often the ghost speaks on normal commands (0 to 1)
  :ghosts         list ghosts
  exit            leave (the ghost will remember)"""


def _enable_windows_ansi() -> None:
    if os.name == "nt":
        os.system("")  # turns on ANSI escape handling in modern Windows terminals


def _short_dir(path: str) -> str:
    home = str(Path.home())
    return "~" + path[len(home):] if path.startswith(home) else path


def _log(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_command(line: str) -> int:
    """Run one command line in the real system shell. cd is handled here so it persists."""
    parts = line.split(None, 1)
    if parts and parts[0] == "cd":
        target = os.path.expanduser(parts[1].strip()) if len(parts) > 1 else str(Path.home())
        try:
            os.chdir(target)
            return 0
        except OSError as exc:
            print(f"cd: {exc}", file=sys.stderr)
            return 1
    try:
        return subprocess.run(line, shell=True).returncode
    except KeyboardInterrupt:
        print()
        return 130


def should_whisper(exit_code: int, omens: list, chance: float) -> bool:
    return exit_code != 0 or bool(omens) or random.random() < chance


def _control(ghost: Ghost, state: dict, line: str) -> None:
    parts = line.split()
    cmd = parts[0]
    if cmd == ":help":
        print(HELP)
    elif cmd == ":ghosts":
        print("  " + ", ".join(PERSONAS))
    elif cmd == ":persona" and len(parts) == 2:
        try:
            ghost.set_persona(parts[1])
            print(f"{PURPLE}  the {parts[1]} awakens.{RESET}")
        except ValueError as exc:
            print(f"  {exc}")
    elif cmd == ":chance" and len(parts) == 2:
        try:
            state["chance"] = max(0.0, min(1.0, float(parts[1])))
            print(f"  ghost speaks {int(state['chance'] * 100)}% of the time "
                  "(always on errors and omens)")
        except ValueError:
            print("  usage: :chance 0.4")
    else:
        print("  unknown control. try :help")


def run_shell(ghost: Ghost, chance: float = 0.4, log_path: Path | None = None) -> None:
    _enable_windows_ansi()
    state = {"chance": chance}
    print(BANNER)
    if ghost.use_model:
        print(f"{DIM}  waking the dead ({ghost.model_id})...{RESET}")
        ghost.load()
    while True:
        try:
            line = input(f"{PURPLE}haunted{RESET}:{_short_dir(os.getcwd())}$ ").strip()
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print()
            break
        if not line:
            continue
        if line in ("exit", "quit"):
            print(f"{PURPLE}{ITAL}  ...you can check out any time you like.{RESET}")
            break
        if line.startswith(":"):
            _control(ghost, state, line)
            continue
        start = time.time()
        code = run_command(line)
        duration = time.time() - start
        omens = find_omens(line)
        if should_whisper(code, omens, state["chance"]):
            print(f"{DIM}  ...{RESET}", end="\r", flush=True)
            text = ghost.whisper(line, code, duration, omens)
            print("\x1b[2K", end="")  # clear the "..." line
            print(f"{PURPLE}{DIM}{ITAL}  ~ {text}{RESET}")
            if log_path:
                _log(log_path, {"cmd": line, "exit": code, "persona": ghost.persona.name,
                                "whisper": text})
