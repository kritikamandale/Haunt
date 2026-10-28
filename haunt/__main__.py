"""CLI:  python -m haunt [shell|whisper|seance|ghosts]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import shell as shell_mod
from .ghost import DEFAULT_MODEL, Ghost
from .history import load_history
from .omens import find_omens
from .personas import DEFAULT_PERSONA, PERSONAS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="haunt", description="A terminal that whispers back.")
    p.add_argument("--persona", default=DEFAULT_PERSONA, choices=list(PERSONAS))
    p.add_argument("--model", default=DEFAULT_MODEL, help="Hugging Face model id")
    p.add_argument("--no-model", action="store_true",
                   help="skip the model and use pre-written whispers (fast, for testing)")
    sub = p.add_subparsers(dest="cmd")

    sh = sub.add_parser("shell", help="start the haunted shell (default)")
    sh.add_argument("--chance", type=float, default=0.4,
                    help="probability of a whisper on normal commands")
    sh.add_argument("--log", action="store_true", help="save whispers to ~/.haunt/whispers.jsonl")

    wh = sub.add_parser("whisper", help="get one whisper for a command, without the shell")
    wh.add_argument("command")
    wh.add_argument("--exit-code", type=int, default=0)

    se = sub.add_parser("seance", help="read your shell history aloud as a ghost story")
    se.add_argument("--limit", type=int, default=25)
    se.add_argument("--history-file", default=None)

    sub.add_parser("ghosts", help="list personas")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cmd = args.cmd or "shell"

    if cmd == "ghosts":
        for name in PERSONAS:
            print(name)
        return 0

    ghost = Ghost(args.persona, use_model=not args.no_model, model_id=args.model)

    if cmd == "whisper":
        print(ghost.whisper(args.command, args.exit_code, 0.0, find_omens(args.command)))
        return 0

    if cmd == "seance":
        cmds = load_history(args.limit, args.history_file)
        if not cmds:
            print("The history is silent. (No history file found.)")
            return 1
        print(f"Reading {len(cmds)} commands (anything secret-looking was skipped)...\n")
        print(ghost.tell_story(cmds))
        return 0

    chance = getattr(args, "chance", 0.4)
    log_path = Path.home() / ".haunt" / "whispers.jsonl" if getattr(args, "log", False) else None
    shell_mod.run_shell(ghost, chance=chance, log_path=log_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
