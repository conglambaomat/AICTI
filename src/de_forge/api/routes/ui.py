from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/review", response_class=HTMLResponse)
def review_page() -> str:
    return """
    <html>
      <head><title>DE-Forge Review</title></head>
      <body>
        <h1>Rule Review</h1>
        <table>
          <thead>
            <tr>
              <th>Evidence quote</th>
              <th>Detection logic</th>
              <th>Sigma condition</th>
              <th>Proof status</th>
              <th>Validation score</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </body>
    </html>
    """
