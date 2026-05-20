# DE-Forge Project Brief

## Mục đích
- **Vấn đề:** Chuyển threat intelligence report thành detection artifacts có thể kiểm chứng (Sigma/KQL), giảm tình trạng sinh rule không bám evidence hoặc không khớp telemetry thực tế.
- **Người dùng:** Detection engineers, SOC analysts, security researchers, và nhóm R&D xây dựng pipeline phát hiện tấn công.
- **Thành công:** Hệ thống chạy end-to-end ổn định, tạo rule bám evidence + telemetry, vượt qua static/dynamic validation, và có thể mở rộng sang benchmark mode.

## Phạm vi (Scope)

### IN-SCOPE (Làm)
- [x] Thiết kế kiến trúc multi-agent theo contract rõ ràng.
- [x] Định nghĩa DetectionSpec bắt buộc làm lớp trung gian.
- [x] Thiết kế pipeline validation tĩnh + động.
- [ ] Triển khai product-mode pipeline từ ingest report đến human review.
- [ ] Triển khai query/rule refinement loop có giới hạn.

### OUT-OF-SCOPE (Không làm ở phase hiện tại)
- Tối ưu benchmark score ngay từ đầu.
- Tích hợp đầy đủ mọi backend SIEM ngay trong MVP.
- Tự động deploy rule vào production không qua human approval.

## Ràng buộc (Constraints)
- **Công nghệ:** Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy, pytest, ruff, mypy.
- **Thời gian:** Ưu tiên triển khai chắc core product-mode trước; benchmark adapter thực hiện sau khi pipeline ổn định.
- **Tài nguyên:** Không giới hạn chi phí mô hình trong giai đoạn thiết kế hệ thống mạnh nhất.
- **Tương thích:** Kiến trúc phải có đường mở rộng để gắn CTI-REALM adapter.

## Yêu cầu phi chức năng
- **Performance:** Pipeline phải có loop giới hạn và runtime dự đoán được.
- **Security:** Không execute nội dung không tin cậy từ report; sanitize input; không lộ secrets.
- **Scalability:** Cho phép mở rộng thêm nguồn telemetry/platform mà không phá contract.
- **Reliability:** Mọi bước có validation gate, trạng thái rõ ràng, và lỗi giải thích được.

## Nguyên tắc kỹ thuật bắt buộc
1. Không sinh rule trực tiếp từ report.
2. Bắt buộc qua DetectionSpec có evidence, ATT&CK mapping, telemetry requirement.
3. Chỉ dùng field telemetry đã được attested.
4. Reviewer/refiner loop phải bounded và có điều kiện abort.
5. Human review là cổng cuối trước export.

## Mốc triển khai ưu tiên
1. Core end-to-end skeleton chạy được.
2. Evidence extraction + ATT&CK mapping + telemetry grounding.
3. DetectionSpec builder + static validation.
4. Query portfolio + Sigma generation + dynamic validation tối thiểu.
5. Reviewer/refiner loop.
6. Benchmark adapter (deferred).

## Tham khảo chính
- CTI-REALM paper: https://arxiv.org/abs/2603.13517
- CTI-REALM implementation: `UKGovernmentBEIS/inspect_evals` (`src/inspect_evals/cti_realm/`)
- Sigma format docs: https://sigmahq.io/docs/basics/rules.html
- MITRE ATT&CK data sources: https://attack.mitre.org/datasources

## Ghi chú
Project ưu tiên “chạy ổn định + đúng + mạnh” trước benchmark; benchmark là pha chứng minh sau khi core quality đã đạt chuẩn.
