from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parents[3] / "brain"

STYLE_FILES = {
    "doctor": ["doctor_style.md"],
    "beauty": ["beauty_style.md", "voice_examples.md"],
}


def load_style(account: str) -> str:
    filenames = STYLE_FILES.get(account)
    if filenames is None:
        raise ValueError(f"Unknown account: {account}")
    parts = [(BRAIN_DIR / filename).read_text(encoding="utf-8") for filename in filenames]
    return "\n\n---\n\n".join(parts)
