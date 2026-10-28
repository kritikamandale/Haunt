"""The ghost: loads an open-weight model with Hugging Face Transformers and whispers.

Default model is Gemma 3 1B (instruction-tuned). It is gated on Hugging Face, so accept the
licence on the model page and log in once. After the first download it runs fully offline.
Override with:  HAUNT_MODEL=Qwen/Qwen2.5-0.5B-Instruct
"""
from __future__ import annotations

import os
import random
import re
import sys

from .personas import DEFAULT_PERSONA, PERSONAS

DEFAULT_MODEL = os.environ.get("HAUNT_MODEL", "google/gemma-3-1b-it")


def clean_whisper(text: str, max_chars: int = 220, max_sentences: int = 2) -> str:
    """Tidy raw model output into a short whisper."""
    text = text.strip().strip('"').strip("'").replace("\n", " ")
    text = re.sub(r"[*_`#>]+", "", text)           # strip markdown
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?…])\s+", text)
    text = " ".join(sentences[:max_sentences])
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "..."
    return text


class Ghost:
    def __init__(self, persona: str = DEFAULT_PERSONA, use_model: bool = True,
                 model_id: str = DEFAULT_MODEL):
        self.persona = PERSONAS[self._check(persona)]
        self.use_model = use_model
        self.model_id = model_id
        self._tok = None
        self._model = None
        self._device = "cpu"
        self.load_error = None

    @staticmethod
    def _check(name: str) -> str:
        if name not in PERSONAS:
            raise ValueError(f"Unknown persona '{name}'. Choices: {', '.join(PERSONAS)}")
        return name

    def set_persona(self, name: str) -> None:
        self.persona = PERSONAS[self._check(name)]

    # ---- model loading -------------------------------------------------
    def load(self) -> bool:
        """Load the model once. Returns True if a model is ready, False to use canned lines."""
        if not self.use_model:
            return False
        if self._model is not None:
            return True
        if self.load_error:
            return False
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.bfloat16 if self._device == "cuda" else torch.float32
            self._tok = AutoTokenizer.from_pretrained(self.model_id)
            try:
                self._model = AutoModelForCausalLM.from_pretrained(self.model_id, dtype=dtype)
            except TypeError:  # older transformers
                self._model = AutoModelForCausalLM.from_pretrained(self.model_id, torch_dtype=dtype)
            self._model.to(self._device).eval()
            return True
        except Exception as exc:  # noqa: BLE001 - fall back on anything
            self.load_error = f"{type(exc).__name__}: {exc}"
            print(f"\x1b[31m[haunt] could not load {self.model_id}: {self.load_error}\x1b[0m",
                  file=sys.stderr)
            print("[haunt] falling back to pre-written whispers.", file=sys.stderr)
            return False

    # ---- generation ----------------------------------------------------
    def _generate(self, prompt: str, max_new_tokens: int, temperature: float = 0.9) -> str:
        import torch

        messages = [{"role": "user", "content": prompt}]
        inputs = self._tok.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt",
        ).to(self._device)
        with torch.no_grad():
            out = self._model.generate(
                **inputs, max_new_tokens=max_new_tokens, do_sample=True,
                temperature=temperature, top_p=0.95,
            )
        new_tokens = out[0][inputs["input_ids"].shape[-1]:]
        return self._tok.decode(new_tokens, skip_special_tokens=True)

    def whisper(self, command: str, exit_code: int = 0, duration: float = 0.0,
                omens: list | None = None) -> str:
        """One short eerie reaction. Only metadata is sent to the model, never command output."""
        if self.load():
            outcome = ("finished normally" if exit_code == 0
                       else f"failed with exit code {exit_code}")
            omen_line = f" Omen: {'; '.join(omens)}." if omens else ""
            prompt = (
                f"{self.persona.system}\n\n"
                "Rules: reply with ONE or TWO short sentences (max 30 words). Stay in character. "
                "No emojis, no markdown, no quotation marks around your reply. "
                "Never give real advice or real commands. Be eerie, not gory.\n\n"
                f"The living just ran this in their terminal:\n  $ {command[:200]}\n"
                f"It {outcome} after {duration:.1f}s.{omen_line}\n\n"
                "Whisper your reply:"
            )
            try:
                text = clean_whisper(self._generate(prompt, max_new_tokens=60))
                if text:
                    return text
            except Exception as exc:  # noqa: BLE001
                self.load_error = f"{type(exc).__name__}: {exc}"
        return self._canned(exit_code)

    def tell_story(self, commands: list) -> str:
        """Turn past commands into a short ghost story (the 'seance')."""
        listing = "\n".join(f"  $ {c[:120]}" for c in commands)
        if self.load():
            prompt = (
                f"{self.persona.system}\n\n"
                "Below are commands someone typed into their terminal over recent nights. "
                "Write a short ghost story (about 120 words) as a haunting reading of this history. "
                "Weave in several of the actual commands by name. Eerie, atmospheric, a little "
                "funny. No markdown, no title.\n\n"
                f"Command history:\n{listing}\n\nThe story:"
            )
            try:
                text = self._generate(prompt, max_new_tokens=260, temperature=0.95).strip()
                if text:
                    return text
            except Exception as exc:  # noqa: BLE001
                self.load_error = f"{type(exc).__name__}: {exc}"
        picks = ", ".join(f"'{c[:30]}'" for c in commands[-3:]) or "nothing at all"
        return ("(offline mode) The history file whispers of " + picks +
                ". Something typed those commands, and it was not entirely you.")

    def _canned(self, exit_code: int) -> str:
        pool = (self.persona.canned_fail if exit_code != 0 and self.persona.canned_fail
                else self.persona.canned)
        return random.choice(pool)
