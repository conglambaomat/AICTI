Hãy thực thi theo Superpowers subagent-driven-development với chất lượng cao nhất.

Yêu cầu bắt buộc:
1) Đọc plan đã duyệt và tách thành task nhỏ.
2) Mỗi task dùng implementer subagent riêng.
3) Sau mỗi task phải review 2 tầng:
   - spec compliance review trước
   - code quality review sau
4) Nếu review có issue thì sửa và review lại đến khi pass.
5) Không sang task tiếp theo khi task hiện tại chưa pass review.
6) Luôn chạy test/verify theo plan.
7) Không code trên main/master nếu chưa có đồng ý rõ ràng.

Khi bị blocker: dừng lại, nêu blocker rõ ràng, hỏi thêm context thay vì đoán.
