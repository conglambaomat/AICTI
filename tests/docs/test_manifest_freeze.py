from pathlib import Path

import yaml


def test_manifest_declares_single_layout_and_authoritative_paths() -> None:
    manifest = yaml.safe_load(
        Path("docs/governance/canonical_manifest.yaml").read_text(encoding="utf-8")
    )
    assert manifest["mode"] == "fail-closed"
    assert "canonical" in manifest["tiers"]
    assert "operational" in manifest["tiers"]
    assert "governance" in manifest["tiers"]
    assert "legacy" in manifest["tiers"]
    for tier in ("canonical", "operational", "governance", "legacy"):
        paths = manifest["tiers"][tier]["paths"]
        assert len(paths) == len(set(paths)), f"duplicate authoritative paths in tier: {tier}"
    for p in manifest["tiers"]["canonical"]["paths"] + manifest["tiers"]["operational"]["paths"]:
        assert Path(p).exists(), f"missing authoritative path: {p}"
    for p in manifest["tiers"]["governance"]["paths"]:
        assert Path(p).exists(), f"missing authoritative path: {p}"
    for p in manifest["tiers"]["legacy"]["paths"]:
        assert Path(p).exists(), f"missing authoritative path: {p}"
