"""Tests for profile-driven KPI thresholds and budgets."""

from de_forge.core.config import Settings
from de_forge.core.constants import PROFILE_THRESHOLDS


def test_profile_thresholds_match_kpi_matrix() -> None:
    """Should expose strict, balanced, exploratory thresholds from KPI matrix."""
    assert PROFILE_THRESHOLDS["strict"]["dynamic_precision_min"] == 0.92
    assert PROFILE_THRESHOLDS["balanced"]["dynamic_precision_min"] == 0.85
    assert PROFILE_THRESHOLDS["exploratory"]["dynamic_precision_min"] == 0.75

    assert PROFILE_THRESHOLDS["strict"]["tokens_per_report_p95_max"] == 120000
    assert PROFILE_THRESHOLDS["balanced"]["tokens_per_report_p95_max"] == 90000
    assert PROFILE_THRESHOLDS["exploratory"]["tokens_per_report_p95_max"] == 70000


def test_settings_load_profile_and_thresholds() -> None:
    """Should load profile and provide matching threshold bundle."""
    settings = Settings(profile="balanced")

    assert settings.profile == "balanced"
    assert settings.profile_thresholds["dynamic_recall_min"] == 0.80
    assert settings.profile_thresholds["cost_per_report_p95_usd_max"] == 2.0


def test_settings_reject_invalid_profile() -> None:
    """Should reject unknown profile values."""
    try:
        Settings(profile="invalid")
        assert False, "Expected ValueError for invalid profile"
    except ValueError:
        assert True
