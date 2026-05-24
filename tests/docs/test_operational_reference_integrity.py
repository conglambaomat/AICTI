from pathlib import Path

REQUIRED_OPERATIONAL_DOCS = [
    "docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md",
    "docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md",
    "docs/operational/AUTONOMOUS_DECISION_POLICY.md",
    "docs/operational/QUALITY_GATES_SOTA_CORE_V2.md",
    "docs/operational/BLOCKERS_AND_ESCALATION.md",
]

ACTIVE_ENTRY_DOCS = [
    Path("CLAUDE.md"),
    Path("README.md"),
    Path("docs/operational/START_HERE_FOR_CLAUDE.md"),
]


def test_required_operational_docs_exist() -> None:
    for p in REQUIRED_OPERATIONAL_DOCS:
        assert Path(p).exists(), f"missing required operational doc: {p}"


def test_active_entry_docs_reference_existing_operational_docs() -> None:
    for doc in ACTIVE_ENTRY_DOCS:
        text = doc.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "docs/operational/" not in line:
                continue
            for token in line.replace("`", " ").replace("(", " ").replace(")", " ").split():
                if token.startswith("docs/operational/") and token.endswith(".md"):
                    assert Path(token).exists(), (
                        f"{doc} references missing operational doc: {token}"
                    )
