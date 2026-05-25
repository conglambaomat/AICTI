from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ui", tags=["ui"])


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html>
  <head><meta charset=\"utf-8\"><title>{title}</title></head>
  <body>
    <h1>DE-Forge UI</h1>
    <p>Non-authoritative static UI shell</p>
    <p>Use API responses for production state</p>
    {body}
  </body>
</html>"""


@router.get("/review", response_class=HTMLResponse)
def review_page() -> str:
    return _page(
        "Review",
        """
        <h2>Review</h2>
        <table>
          <thead>
            <tr>
              <th>Evidence quote</th>
              <th>Detection logic</th>
              <th>Sigma condition</th>
              <th>Proof status</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
        """,
    )


@router.get("/reports", response_class=HTMLResponse)
def reports_page() -> str:
    return _page("Reports", "<h2>Reports</h2>")


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail_page(run_id: str) -> str:
    return _page("Run Detail", f"<h2>Run Detail</h2><p>{run_id}</p>")


@router.get("/runs/{run_id}/evidence-spec", response_class=HTMLResponse)
def evidence_spec_page(run_id: str) -> str:
    return _page(
        "Evidence + DetectionSpec",
        f"""
        <h2>Evidence + DetectionSpec</h2>
        <p>{run_id}</p>
        <ul>
          <li>Lineage</li>
          <li>Citation</li>
          <li>Validation</li>
          <li>Oracle</li>
        </ul>
        """,
    )


@router.get("/runs/{run_id}/portfolio-review", response_class=HTMLResponse)
def portfolio_review_page(run_id: str) -> str:
    return _page(
        "Rule Portfolio + Review",
        f"""
        <h2>Rule Portfolio + Review</h2>
        <p>{run_id}</p>
        <ul>
          <li>Evidence quote</li>
          <li>Detection logic</li>
          <li>Sigma condition</li>
          <li>Proof status</li>
        </ul>
        <form>
          <label>Reviewer</label>
          <input type=\"text\" name=\"reviewer\" />
          <button type=\"submit\">Approve</button>
          <button type=\"submit\">Reject</button>
        </form>
        """,
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> str:
    return _page(
        "Ops Dashboard",
        """
        <h2>Ops Dashboard</h2>
        <p>Queue</p>
        <div>Filter</div>
        <div>Sort</div>
        <div>Search</div>
        <div>Saved view</div>
        """,
    )
