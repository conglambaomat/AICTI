from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


def git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *cmd], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("DOCS_PREFLIGHT: FAIL git metadata unavailable")
        raise SystemExit(1)


def main() -> int:
    manifest_path = Path("docs/governance/canonical_manifest.yaml")
    if not manifest_path.exists():
        print("DOCS_PREFLIGHT: FAIL missing manifest")
        return 1

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    try:
        missing: list[str] = []
        for tier in ("canonical", "operational", "governance", "legacy"):
            for p in manifest["tiers"][tier]["paths"]:
                if not Path(p).exists():
                    missing.append(p)
    except (TypeError, KeyError):
        print("DOCS_PREFLIGHT: FAIL invalid manifest schema")
        return 1

    branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    sha = git(["rev-parse", "HEAD"])
    print(f"BRANCH: {branch}")
    print(f"COMMIT_SHA: {sha}")
    print("LAYOUT: canonical/operational/governance/legacy")

    if missing:
        print("DOCS_PREFLIGHT: FAIL missing authoritative paths")
        for p in missing:
            print(f"- {p}")
        return 1

    print("DOCS_PREFLIGHT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
