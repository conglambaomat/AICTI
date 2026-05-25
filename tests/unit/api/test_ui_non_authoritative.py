from de_forge.api.routes.ui import (
    dashboard_page,
    evidence_spec_page,
    portfolio_review_page,
    review_page,
)


def test_static_ui_shell_pages_are_labeled_non_authoritative() -> None:
    pages = [
        review_page(),
        evidence_spec_page("run-123"),
        portfolio_review_page("run-123"),
        dashboard_page(),
    ]

    for html in pages:
        assert "Non-authoritative static UI shell" in html
        assert "Use API responses for production state" in html
