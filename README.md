# OrganizationAI — Policy hoàn ứng câu lạc bộ

Kho lưu trữ này là gói Policy có thể dùng làm nguồn quy tắc cho agent hỗ trợ thủ quỹ câu lạc bộ sinh viên. Gói bao quát hai luồng: quyết toán tiền đã tạm ứng và hoàn trả khoản thành viên đã chi hộ.

> Đây là mẫu chung, không phải ý kiến pháp lý và không tự tạo quyền chi tiền. Trường/Đoàn/Hội hoặc đơn vị chủ quản phải xác nhận các trường cấu hình trước khi vận hành thật. Agent chỉ lập và đánh dấu hồ sơ đủ điều kiện; thủ quỹ hoặc hệ thống được ủy quyền mới giải ngân.

## Bộ bàn giao

- `Policy_Hoan_Ung_CLB.docx`: quy định nghiệp vụ, biểu mẫu và phụ lục dành cho con người.
- `policy_rules.yaml`: quy tắc máy đọc được, có mã, nguồn, ưu tiên, điều kiện và kết quả.
- `reimbursement.schema.json`: JSON Schema cho hồ sơ, cấu hình, quyết định, chuyển tiếp và audit.
- `test_cases.json`: 16 ca kiểm thử tổng hợp, không chứa dữ liệu thật.
- `verify_cases.json`: 5 ca chạy nhanh theo Task A (3 tự động, 2 chuyển tiếp).

## Hợp đồng quyết định

Agent chỉ trả một trong sáu trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| `AUTO_PROCESS` | Hồ sơ thường quy, đầy đủ, trong ngân sách/thẩm quyền; lập bộ hồ sơ đủ điều kiện thanh toán. |
| `NEEDS_FACT` | Chưa xác định được sự thật; bắt buộc hỏi và chờ. |
| `OUT_OF_POLICY` | Khoản chi ngoài phạm vi hoặc cần ngoại lệ. |
| `AUTHORITY_REQUIRED` | Vượt ngưỡng, vượt ngân sách, xung đột lợi ích hoặc cần người có thẩm quyền. |
| `REJECTED_BY_RULE` | Dữ liệu đã xác minh vi phạm quy tắc tuyệt đối, ví dụ chứng từ trùng đã thanh toán. |
| `PAUSED` | Hồ sơ/hệ thống bị người có thẩm quyền dừng. |

Ba loại chuyển tiếp chuẩn là `FACT_UNKNOWN`, `OUT_OF_POLICY`, `AUTHORITY_REQUIRED`. Dữ liệu đã bị gắn cờ nghi vấn không bao giờ được kết luận `AUTO_PROCESS` hoặc `REJECTED_BY_RULE`.

## Thứ tự đánh giá

1. Trạng thái dừng; khả năng đọc và tính toàn vẹn dữ liệu.
2. Trùng lặp hoặc dấu hiệu gian lận.
3. Phạm vi, mục đích và danh mục chi.
4. Thành phần hồ sơ bắt buộc.
5. Ngân sách, xung đột lợi ích và thẩm quyền.
6. Hóa đơn, phương thức thanh toán và điều kiện thuế.
7. Phép tính và quyết định cuối cùng.

Khi nhiều quy tắc cùng kích hoạt, ưu tiên quy tắc có `priority` nhỏ hơn. Nếu quy tắc nội bộ xung đột, áp dụng phương án hạn chế hơn và chuyển tiếp; phê duyệt nội bộ không được ghi đè yêu cầu pháp luật bắt buộc.

## Ánh xạ vào rule engine hoặc LLM agent

1. Nạp `OrganizationProfile` và khóa `policy_version` cho mỗi lần chạy.
2. Chuẩn hóa đầu vào theo `$defs/ReimbursementCase` trong schema; lưu hash tệp thay vì dựa vào tên tệp.
3. Chạy quy tắc theo `evaluation_order`; mỗi lần kích hoạt ghi `rule_id`, bằng chứng và snapshot đầu vào vào `AuditEvent`.
4. Nếu có `suspected=true`, OCR thấp, mâu thuẫn số liệu hoặc thiếu sự thật: tạo `Escalation` loại `FACT_UNKNOWN` và dừng suy luận khẳng định.
5. Chỉ chạy công thức sau khi từng dòng chi có kết quả `ACCEPTED` hoặc `NOT_ACCEPTED` dựa trên dữ liệu đã xác minh.
6. Với chuyển tiếp, câu hỏi phải nêu mã hồ sơ, dòng chi/chứng từ, dữ kiện đã biết, điều cần xác nhận, định dạng trả lời và bước agent sẽ tiếp tục.
7. `AUTO_PROCESS` chỉ sinh gói đề nghị thanh toán; không gọi API chuyển tiền.
8. Mọi `override`/`undo` phải có tác nhân, vai trò, lý do, thời gian và liên kết quyết định trước đó.

Ví dụ pseudo-code:

```text
validate_schema(case)
if profile.system_paused: PAUSED
for rule in rules.sorted_by(priority):
    result = evaluate(rule, case, profile)
    append_audit(result)
    if result.is_terminal_or_escalation: return result
calculate_verified_amounts()
return AUTO_PROCESS
```

## Cấu hình bắt buộc trước pilot

Xác nhận tối thiểu: đơn vị chủ quản và chế độ kế toán/thuế áp dụng; vai trò phê duyệt; ngân sách; danh mục được phép/có điều kiện/cấm; hạn nộp; ngưỡng tự động; quy tắc cộng gộp; yêu cầu hóa đơn/chứng từ; kênh chuyển tiếp; thời hạn lưu trữ; người được phép pause/override/undo.

Các mặc định mẫu: VND; hạn nộp 10 ngày làm việc; tự xử lý đến 5.000.000 đồng; trên 5.000.000 đồng cần Chủ nhiệm; kiểm tra chứng từ thanh toán không dùng tiền mặt từ 5.000.000 đồng khi chế độ thuế tương ứng áp dụng; cộng gộp cùng nhà cung cấp/ngày/mục đích; đồ uống có cồn ngoài Policy; không tự phê duyệt.

## Chạy kiểm tra

```bash
python3 -m json.tool reimbursement.schema.json >/dev/null
python3 -m json.tool test_cases.json >/dev/null
python3 -m json.tool verify_cases.json >/dev/null
python3 -c "import yaml; yaml.safe_load(open('policy_rules.yaml'))"
```

Tiêu chí Verify: 3/3 ca thường quy tự động; 2/2 ca cần chuyển tiếp được phát hiện; không khẳng định khi dữ liệu nghi vấn; câu hỏi đủ ngữ cảnh; cùng đầu vào và Policy cho cùng kết quả. Báo cáo:

- Tỷ lệ bỏ sót chuyển tiếp = ca cần chuyển tiếp nhưng tự động / tổng ca cần chuyển tiếp.
- Tỷ lệ chuyển tiếp không cần thiết = ca thường quy bị chuyển tiếp / tổng ca thường quy.

## Cơ sở tham chiếu

Policy được rà soát đến ngày 12/09/2026 theo Luật Kế toán 88/2015/QH13; chế độ kế toán áp dụng cho đơn vị chủ quản; quy định hiện hành về hóa đơn, thuế, thanh toán không dùng tiền mặt và bảo vệ dữ liệu cá nhân. Mẫu tương thích về trường thông tin với 04-TT và 05-TT của Thông tư 99/2025/TT-BTC, nhưng không mặc định chế độ kế toán doanh nghiệp áp dụng trực tiếp cho mọi câu lạc bộ. Chi tiết URL và điều kiện áp dụng nằm trong DOCX và YAML.
