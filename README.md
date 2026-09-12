# OrganizationAI — Policy hoàn ứng câu lạc bộ

Kho lưu trữ này là gói Policy có thể dùng làm nguồn quy tắc cho agent hỗ trợ thủ quỹ câu lạc bộ sinh viên. Gói bao quát hai luồng: quyết toán tiền đã tạm ứng và hoàn trả khoản thành viên đã chi hộ.

> Đây là mẫu chung, không phải ý kiến pháp lý và không tự tạo quyền chi tiền. Trường/Đoàn/Hội hoặc đơn vị chủ quản phải xác nhận các trường cấu hình trước khi vận hành thật. Agent chỉ kiểm tra, tính toán, phân loại và lập gói hồ sơ; không phê duyệt, từ chối hay giải ngân. Quyết định cuối cùng thuộc người có thẩm quyền.

## Bộ bàn giao

- [`Policy_Hoan_Ung_CLB.md`](Policy_Hoan_Ung_CLB.md): nguồn nội dung chính, đọc và chỉnh sửa trực tiếp trên GitHub.
- [`policy_rules.yaml`](policy_rules.yaml): quy tắc máy đọc được, có mã, nguồn, ưu tiên, điều kiện và kết quả.
- [`reimbursement.schema.json`](reimbursement.schema.json): JSON Schema cho hồ sơ, cấu hình, kết quả xử lý, chuyển tiếp và audit.
- [`test_cases.json`](test_cases.json): 16 ca kiểm thử tổng hợp, không chứa dữ liệu thật.
- [`verify_cases.json`](verify_cases.json): 5 ca chạy nhanh theo Task A (3 thường quy, 2 chuyển tiếp).

## Chỉnh sửa Policy trên GitHub

1. Mở [`Policy_Hoan_Ung_CLB.md`](Policy_Hoan_Ung_CLB.md).
2. Chọn biểu tượng bút chì **Edit this file**.
3. Tạo nhánh mới, ghi nội dung thay đổi và mở Pull Request để review.
4. Sau khi nội dung được duyệt, cập nhật phiên bản Policy và các tệp quy tắc liên quan nếu logic thay đổi.

`Policy_Hoan_Ung_CLB.md` là nguồn nội dung dành cho con người và là bản Policy duy nhất được duy trì trong repository.

## Hợp đồng đầu ra

Agent chỉ phân loại kết quả xử lý, không dự đoán hay ban hành quyết định phê duyệt:

| Trường | Giá trị | Ý nghĩa |
|---|---|---|
| `processing_result` | `ROUTINE_PROCESSED` | Hồ sơ thường quy đã được kiểm tra, tính toán và lập gói để người có thẩm quyền xem xét. |
| `processing_result` | `ESCALATED` | Agent dừng xử lý thường quy và tạo yêu cầu chuyển tiếp. |
| `escalation_type` | `FACT_UNKNOWN` | Chưa xác định được thông tin thực tế; phải hỏi và chờ dữ kiện. |
| `escalation_type` | `OUT_OF_POLICY` | Khoản chi nằm ngoài Policy hoặc cần xem xét ngoại lệ. |
| `escalation_type` | `AUTHORITY_REQUIRED` | Vượt ngưỡng/ngân sách, có xung đột lợi ích hoặc cần người có thẩm quyền. |
| `approval_status` | `PENDING_HUMAN_APPROVAL` | Mọi hồ sơ đều chờ con người phê duyệt; agent không được đổi giá trị này. |
| `control_state` | `ACTIVE` hoặc `PAUSED` | Trạng thái vận hành riêng, không phải nhãn dự đoán. |

Khi `processing_result=ROUTINE_PROCESSED`, `escalation_type` phải là `null`. Khi `processing_result=ESCALATED`, `escalation_type` bắt buộc là đúng một trong ba loại trên. Dữ liệu bị gắn cờ nghi vấn chỉ được trả `ESCALATED/FACT_UNKNOWN`; agent không được đưa ra kết luận khẳng định, phê duyệt hoặc từ chối.

## Thứ tự đánh giá

1. Trạng thái dừng; khả năng đọc và tính toàn vẹn dữ liệu.
2. Trùng lặp hoặc dấu hiệu gian lận.
3. Phạm vi, mục đích và danh mục chi.
4. Thành phần hồ sơ bắt buộc.
5. Ngân sách, xung đột lợi ích và thẩm quyền.
6. Hóa đơn, phương thức thanh toán và điều kiện thuế.
7. Phép tính và phân loại kết quả xử lý.

Khi nhiều quy tắc cùng kích hoạt, ưu tiên quy tắc có `priority` nhỏ hơn. Nếu quy tắc nội bộ xung đột, áp dụng phương án hạn chế hơn và chuyển tiếp; phê duyệt nội bộ không được ghi đè yêu cầu pháp luật bắt buộc.

## Ánh xạ vào rule engine hoặc LLM agent

1. Nạp `OrganizationProfile` và khóa `policy_version` cho mỗi lần chạy.
2. Chuẩn hóa đầu vào theo `$defs/ReimbursementCase` trong schema; lưu hash tệp thay vì dựa vào tên tệp.
3. Chạy quy tắc theo `evaluation_order`; mỗi lần kích hoạt ghi `rule_id`, bằng chứng và snapshot đầu vào vào `AuditEvent`.
4. Nếu có `suspected=true`, OCR thấp, mâu thuẫn số liệu hoặc thiếu sự thật: tạo `Escalation` loại `FACT_UNKNOWN` và dừng suy luận khẳng định.
5. Chỉ chạy công thức sau khi từng dòng chi đã có `line_assessment` dựa trên dữ liệu xác minh; chỉ cộng dòng `ELIGIBLE`.
6. Với chuyển tiếp, câu hỏi phải nêu mã hồ sơ, dòng chi/chứng từ, dữ kiện đã biết, điều cần xác nhận, định dạng trả lời và bước agent sẽ tiếp tục.
7. `ROUTINE_PROCESSED` chỉ xác nhận agent đã hoàn tất khâu hỗ trợ nghiệp vụ; `approval_status` vẫn là `PENDING_HUMAN_APPROVAL`.
8. Agent không được phê duyệt, từ chối hoặc gọi API chuyển tiền. Chứng từ trùng đã xác minh cũng phải chuyển tiếp `OUT_OF_POLICY` để con người quyết định.
9. Mọi `override`/`undo` phải có tác nhân, vai trò, lý do, thời gian và liên kết kết quả trước đó.

Ví dụ pseudo-code:

```text
validate_schema(case)
if control_state == PAUSED: halt_without_prediction()
for rule in rules.sorted_by(priority):
    result = evaluate(rule, case, profile)
    append_audit(result)
    if result.requires_escalation:
        return ESCALATED, result.escalation_type, PENDING_HUMAN_APPROVAL
calculate_verified_amounts()
generate_review_packet()
return ROUTINE_PROCESSED, null, PENDING_HUMAN_APPROVAL
```

## Cấu hình bắt buộc trước pilot

Xác nhận tối thiểu: đơn vị chủ quản và chế độ kế toán/thuế áp dụng; vai trò phê duyệt; ngân sách; danh mục được phép/có điều kiện/cấm; hạn nộp; ngưỡng xử lý thường quy; quy tắc cộng gộp; yêu cầu hóa đơn/chứng từ; kênh chuyển tiếp; thời hạn lưu trữ; người được phép pause/override/undo.

Các mặc định mẫu: VND; hạn nộp 10 ngày làm việc; xử lý thường quy đến 5.000.000 đồng; trên 5.000.000 đồng chuyển tiếp Chủ nhiệm; kiểm tra chứng từ thanh toán không dùng tiền mặt từ 5.000.000 đồng khi chế độ thuế tương ứng áp dụng; cộng gộp cùng nhà cung cấp/ngày/mục đích; đồ uống có cồn ngoài Policy; mọi hồ sơ chờ con người phê duyệt.

## Chạy kiểm tra

```bash
python3 -m json.tool reimbursement.schema.json >/dev/null
python3 -m json.tool test_cases.json >/dev/null
python3 -m json.tool verify_cases.json >/dev/null
python3 -c "import yaml; yaml.safe_load(open('policy_rules.yaml'))"
```

Tiêu chí Verify: 3/3 ca thường quy được xử lý; 2/2 ca cần chuyển tiếp được phát hiện; không khẳng định khi dữ liệu nghi vấn; không tự động phê duyệt/từ chối; câu hỏi đủ ngữ cảnh; cùng đầu vào và Policy cho cùng kết quả. Báo cáo:

- Tỷ lệ bỏ sót chuyển tiếp = ca cần chuyển tiếp nhưng bị phân loại thường quy / tổng ca cần chuyển tiếp.
- Tỷ lệ chuyển tiếp không cần thiết = ca thường quy bị chuyển tiếp / tổng ca thường quy.

## Cơ sở tham chiếu

Policy được rà soát đến ngày 12/09/2026 theo Luật Kế toán 88/2015/QH13; chế độ kế toán áp dụng cho đơn vị chủ quản; quy định hiện hành về hóa đơn, thuế, thanh toán không dùng tiền mặt và bảo vệ dữ liệu cá nhân. Mẫu tương thích về trường thông tin với 04-TT và 05-TT của Thông tư 99/2025/TT-BTC, nhưng không mặc định chế độ kế toán doanh nghiệp áp dụng trực tiếp cho mọi câu lạc bộ. Chi tiết URL và điều kiện áp dụng nằm trong bản Policy Markdown và YAML.
