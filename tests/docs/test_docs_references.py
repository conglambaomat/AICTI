from pathlib import Path

ACTIVE_DOCS = [
    Path("CLAUDE.md"),
    Path("README.md"),
    Path("docs/operational/START_HERE_FOR_CLAUDE.md"),
]

BANNED_ACTIVE_PATTERNS = [
    "docs/legacy/",
]


def test_active_docs_do_not_reference_legacy_as_authority() -> None:
    for p in ACTIVE_DOCS:
        text = p.read_text(encoding="utf-8")
        for pattern in BANNED_ACTIVE_PATTERNS:
            assert pattern not in text, f"{p} references legacy authority: {pattern}"
