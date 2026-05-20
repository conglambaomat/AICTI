# PHÂN TÍCH PROMPT HIỆN TẠI

## Điểm mạnh
1. **Rõ ràng về autonomy contract** - định nghĩa khi nào dừng
2. **Hard requirements cụ thể** - model lock, workflow bắt buộc
3. **Source of truth hierarchy** - ưu tiên tài liệu rõ ràng
4. **Definition of done strict** - tiêu chí hoàn thành đo được

## Vấn đề nghiêm trọng làm giảm hiệu quả

### 1. **Xung đột với Superpowers workflow**
- Prompt yêu cầu "bắt đầu ngay lập tức" nhưng Superpowers bắt buộc brainstorming trước
- Hook gate đã set sẽ chặn Write/Edit nếu chưa có spec/plan
- Tạo deadlock: prompt bảo "làm ngay", hook bảo "chưa được"

### 2. **Quá chi tiết execution plan làm mất tính linh hoạt**
- Liệt kê 10 bước pipeline cụ thể → agent sẽ follow máy móc thay vì adapt
- Superpowers writing-plans skill đã làm việc này tốt hơn (chia task động)
- Duplicate effort: prompt đã plan sẵn + agent phải plan lại theo Superpowers

### 3. **Thiếu context về trạng thái hiện tại**
- Không nói rõ project đang ở đâu (empty repo? có code sẵn?)
- Không nói rõ docs nào đã có, nào chưa có
- Agent sẽ lãng phí token đọc lại toàn bộ thay vì focus vào gap

### 4. **Subagent rules quá verbose**
- Superpowers subagent-driven-development skill đã có rules này
- Lặp lại làm prompt dài, tăng nguy cơ agent bỏ qua

### 5. **Model lock conflict**
- Prompt lock `cx/default` nhưng settings.json đã set `opus`
- Tạo mâu thuẫn → agent không biết nghe ai

### 6. **Thiếu checkpoint strategy**
- "Không hỏi lại xác nhận tiến độ" nguy hiểm cho dự án lớn
- Nếu sai hướng từ đầu, sẽ lãng phí hàng giờ token trước khi phát hiện

## Đề xuất cải thiện

### Nguyên tắc thiết kế prompt tối ưu cho Claude CLI + Superpowers:
1. **Leverage, don't duplicate** - dùng Superpowers skills thay vì viết lại logic
2. **Context-aware** - nói rõ trạng thái hiện tại
3. **Checkpoint-friendly** - cho phép validation ở các mốc quan trọng
4. **Conflict-free** - không xung đột với settings/hooks
5. **Concise** - ngắn gọn, dễ parse, giảm token waste

---

# PHIÊN BẢN TỐI ƯU HÓA

Dưới đây là prompt được thiết kế lại để:
- Tương thích 100% với Superpowers workflow
- Tận dụng skills có sẵn thay vì duplicate
- Ngắn gọn hơn 60% nhưng hiệu quả hơn
- Có checkpoint hợp lý
- Không xung đột config
