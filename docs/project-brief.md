# DE-Forge Project Brief

## Mục đích

- **Vấn đề:** Chuyển threat intelligence report thành detection artifacts có thể kiểm chứng, giảm tình trạng sinh rule không bám evidence hoặc không khớp telemetry thực tế.
- **Người dùng:** Detection engineers, SOC analysts, security researchers, và nhóm R&D xây dựng pipeline phát hiện tấn công.
- **Thành công:** Hệ thống chạy end-to-end ổn định tới human review, tạo rule bám evidence + telemetry, vượt qua validation/proof gates, và có thể mở rộng sang benchmark mode sau khi core ổn định.

## Source of truth hiện tại

DE-Forge hiện theo kiến trúc **SOTA Core v2**. Claude CLI phải đọc trước:

- `docs/operational/START_HERE_FOR_CLAUDE.md`
- `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`
- `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`

Các tài liệu MVP/Agentic Deep-Analysis cũ từ 2026-05-20 chỉ còn giá trị tham khảo lịch sử và không được dùng làm hướng triển khai nếu mâu thuẫn với SOTA Core v2.

## Phạm vi hiện tại

### IN-SCOPE

- [x] Thiết kế kiến trúc multi-agent theo contract rõ ràng.
- [x] Định nghĩa DetectionSpec bắt buộc làm lớp trung gian.
- [x] Thiết kế evidence graph, proof obligations, oracle evaluation, validation và regression gates.
- [ ] Triển khai deterministic foundation.
- [ ] Triển khai Detection AST + Sigma compiler.
- [ ] Triển khai validation/oracle/regression services.
- [ ] Triển khai controlled agents.
- [ ] Triển khai orchestrator, API, UI tối thiểu, dashboard.

### OUT-OF-SCOPE ban đầu

- Multi-user hoặc multi-tenant enterprise features.
- Billing, organizations, RBAC, SaaS administration.
- Auto-deploy rule vào production SIEM không qua human approval.
- OCR cho scanned/image-only reports.
- Tối ưu benchmark score trước khi product-mode core ổn định.

## Nguyên tắc kỹ thuật bắt buộc

1. Không sinh production rule trực tiếp từ report.
2. Bắt buộc đi qua Evidence Graph và verified DetectionSpec.
3. Bắt buộc dùng Detection AST/compiler khi sinh Sigma production candidate.
4. Citation phải exact và verified.
5. ATT&CK modeling dùng:

```text
Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field
```

6. Required proof obligations phải proven trước final candidate selection.
7. Oracle data, khi có, là authoritative cho evaluation.
8. Feedback review phải tạo regression protection.
9. Human review là cổng cuối trước export.
10. Agent/refinement loops phải bounded.

## Mốc triển khai ưu tiên

1. Deterministic foundation: hashing, idempotency, persistence, evidence graph, citation verifier, telemetry/ATT&CK registries, DetectionSpec verifier, proof obligations.
2. Detection AST + Sigma compiler.
3. Static/dynamic/adversarial/counterfactual validation, oracle evaluation, feedback regression.
4. Controlled LLM agents with strict IO envelope and audit persistence.
5. Orchestrator, auto/cautious modes, API, minimal trust-oriented review UI, quality dashboard.
6. Future benchmark adapter, including CTI-REALM compatibility, after product-mode quality is stable.

## Ràng buộc

- **Công nghệ:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest, ruff, mypy.
- **Runtime local:** SQLite default; schema should remain PostgreSQL-compatible for future migration.
- **Model:** OpenAI-compatible provider at `https://shopapikey.com/v1`, model `cx/gpt-5.5`, API key env var `OPENAI_API_KEY`.
- **Security:** Không execute nội dung không tin cậy từ report; không log secrets; không bypass citation/proof gates.

## Tham khảo chính

- SOTA Core v2 design: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- CTI-REALM paper: https://arxiv.org/abs/2603.13517
- CTI-REALM implementation: `UKGovernmentBEIS/inspect_evals` (`src/inspect_evals/cti_realm/`)
- Sigma format docs: https://sigmahq.io/docs/basics/rules.html
- MITRE ATT&CK detections/data components should be modeled through SOTA Core v2's Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field path. Do not center implementation on deprecated ATT&CK Data Source framing.

## Ghi chú

Project ưu tiên “chạy ổn định + đúng + mạnh” trước benchmark. Benchmark là pha chứng minh sau khi core quality đã đạt chuẩn.
