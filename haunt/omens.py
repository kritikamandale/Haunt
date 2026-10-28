"""Rule-based 'omens': spots risky-looking commands so the ghost can react to them.
No model needed here, it is just regex. Easy to extend."""
import re

OMENS = [
    (r"\brm\s+(-\w*r\w*f|-\w*f\w*r)\b", "it is deleting things recursively and by force"),
    (r"\bsudo\b", "it is summoning root powers"),
    (r"git\s+push\s+.*(--force|-f)\b", "it is force-pushing over history"),
    (r"git\s+reset\s+--hard", "it is erasing uncommitted work"),
    (r"\bchmod\s+(-R\s+)?777\b", "it is opening every door in the house"),
    (r"\b(kill|pkill|killall)\b", "it is ending a process"),
    (r"\b(shutdown|reboot|halt|poweroff)\b", "it is trying to put the machine to sleep"),
    (r"\bdrop\s+(table|database)\b", "it is dropping a database"),
    (r"\bdd\s+if=", "it is writing raw bytes to a disk"),
    (r":\(\)\s*\{", "it looks like a fork bomb"),
    (r"\bformat\b|\bdel\s+/[sfq]", "it is wiping something away"),
    (r"\bcurl\b.*\|\s*(ba)?sh", "it is running a stranger's script"),
    (r"\bcat\s+.*\.(env|pem)\b", "it is peeking at secrets"),
]


def find_omens(command: str) -> list:
    return [label for pattern, label in OMENS if re.search(pattern, command, re.I)]
