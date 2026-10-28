from haunt.ghost import Ghost, clean_whisper
from haunt.history import load_history
from haunt.omens import find_omens
from haunt.personas import PERSONAS


def test_omens_detect_risky_commands():
    assert find_omens("sudo rm -rf /tmp/x")
    assert find_omens("git push --force origin main")
    assert find_omens("ls -la") == []


def test_clean_whisper_limits_sentences_and_markdown():
    assert clean_whisper('"**One.** Two. Three. Four."') == "One. Two."


def test_ghost_offline_returns_text_for_every_persona():
    for name in PERSONAS:
        g = Ghost(name, use_model=False)
        assert g.whisper("ls", 0, 0.1)
        assert g.whisper("make", 2, 0.1)


def test_history_skips_secrets_and_dupes(tmp_path):
    f = tmp_path / "h"
    f.write_text("ls\nexport API_KEY=abc\nls\ngit status\n")
    assert load_history(10, str(f)) == ["ls", "git status"]
