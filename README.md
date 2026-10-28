# haunt - a terminal that whispers back

A tiny haunted shell. You type commands as usual; after each one, a ghost running on a
**local open-weight model (Gemma via Hugging Face Transformers)** may whisper an eerie comment.

Built for the Hacktoberfest Open-Source AI Challenge, Week 4: *Ghost in the Machine*.

## Why open models matter here
- **Private**: the ghost only sees the command text, exit code, and duration, never output, and nothing leaves your machine.
- **Offline**: after the first download it works with the Wi-Fi off.
- **Swappable**: change the model with `HAUNT_MODEL=...` or the persona with `--persona`.
- **Free**: no API key, no per-token cost.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Gemma is gated: accept the licence at https://huggingface.co/google/gemma-3-1b-it
pip install -U huggingface_hub
huggingface-cli login              # paste a read token (newer versions: `hf auth login`)
```

## Run
```bash
python -m haunt                      # haunted shell (default persona: sysadmin)
python -m haunt --persona ofrenda    # gentle Dia de los Muertos / diya spirit
python -m haunt whisper "rm -rf build" --exit-code 0
python -m haunt seance               # ghost story from your shell history (secrets skipped)
python -m haunt --no-model           # pre-written whispers, instant, no download
HAUNT_MODEL=Qwen/Qwen2.5-0.5B-Instruct python -m haunt   # un-gated alternative
```
Inside the shell: `:help`, `:persona victorian`, `:chance 0.8`, `:ghosts`, `exit`.

## How it works
| File | Job |
|---|---|
| `haunt/shell.py` | REPL: runs commands in the real shell (`cd` handled so it persists), decides when to whisper |
| `haunt/ghost.py` | Loads the model with Transformers, builds the prompt, cleans the output, falls back to canned lines |
| `haunt/personas.py` | The ghosts and their system prompts |
| `haunt/omens.py` | Regex "omens" for risky commands (`sudo`, `rm -rf`, `git push --force`...) |
| `haunt/history.py` | Reads bash/zsh/PowerShell history for `seance`, skipping secret-looking lines |

The ghost always speaks on errors and omens, and randomly (`--chance`) otherwise, so latency stays tolerable on CPU.

## Dev
```bash
pip install -r requirements-dev.txt
pytest
```
See `docs/TODO.md` for upgrade ideas and `docs/POST_OUTLINE.md` for the DEV post.
