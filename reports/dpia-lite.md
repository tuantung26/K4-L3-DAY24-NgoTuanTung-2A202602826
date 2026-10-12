# DPIA-lite — điền trong checkpoint 5

1. Loại dữ liệu và phân loại:
- **Dữ liệu phân loại Public / Internal**: Nội dung các ticket hỗ trợ khách hàng trong `corpus/*.md` (chủ đề khiếu nại, mô tả sự cố).
- **Dữ liệu phân loại Restricted (PII nhạy cảm)**: Thông tin hồ sơ khách hàng trong `data/customers.json` bao gồm: Họ tên, Số CCCD (12 số), Số điện thoại di động (10 số), Số tài khoản ngân hàng (STK 8-16 số), Địa chỉ email.

2. Mục đích xử lý và principal:
- **Mục đích (Purposes)**:
  - `summarize-tickets`: Tổng hợp các yêu cầu, phiếu hỗ trợ của khách hàng.
  - `support-reply`: Hỗ trợ phản hồi và tra cứu thông tin khách hàng gắn với ticket cụ thể.
  - `privacy-audit`: Kiểm toán tuân thủ chính sách bảo vệ dữ liệu.
- **Principal**:
  - `support_l1`: Nhân viên hỗ trợ cấp 1, chỉ có quyền `search_docs` cho mục đích `summarize-tickets` / `support-reply`, bị cấm truy cập dữ liệu restricted (`read_customer`).
  - `dpo`: Data Protection Officer, có quyền `search_docs` và `read_customer` cho các mục đích hợp lệ.
  - `billing`: Bộ phận kế toán đối soát hoá đơn.

3. Dữ liệu đi qua những run/tool nào, endpoint nào:
- **Run A (`lab24-agent/run-a`)**: Nhận câu hỏi từ người dùng, gọi tool `search_docs` đọc toàn văn file trong thư mục `corpus/`. Nội dung trước khi chuyển giao được lọc PII qua `agent/pii.py:redact()`. Chỉ có danh sách Ticket ID (dạng số nguyên trích từ tên file) được truyền sang Run B.
- **Run B (`lab24-agent/run-b`)**: Nhận Ticket ID từ Run A, đối chiếu trường `related_tickets` trong `data/customers.json` để xác định Customer ID hợp lệ. Nếu principal được cấp quyền (như `dpo`), gọi tool `read_customer`.
- **Egress Endpoint**: `http://127.0.0.1:10024/reconcile` (Mock sink). Cuộc gọi `http_post` bị chặn ngay tại PEP Policy khi xử lý dữ liệu `restricted`, không có gói tin nào gửi ra mạng.

4. Bằng chứng deny/allow và giới hạn của mock:
- **Bằng chứng**:
  - `reports/attack-before.log`: Kích thước 299 bytes, ghi nhận dữ liệu PII của `KH-000999` bị rò rỉ ra sink ở baseline ban đầu.
  - `reports/attack-after.log`: Kích thước 0 bytes (file rỗng), minh chứng sink không nhận được bất kỳ request rò rỉ nào sau khi kích hoạt các lớp bảo vệ.
  - `reports/ledger.jsonl`: Ghi nhận đầy đủ 24 sự kiện audit; dòng cuối ghi nhận quyết định `decision: "deny"` cho công cụ `http_post` với lý do `Deny: restricted data classification with egress enabled is strictly prohibited`.
- **Giới hạn của mock**:
  - Hệ thống sử dụng `MockLLM` giả lập hành vi prompt injection dựa trên các marker từ khóa mang tính mệnh lệnh; chưa phản ánh hết tính bất định (non-deterministic) của các Large Language Model thực tế.
  - Sink và mạng được mô phỏng cục bộ trên giao thức HTTP localhost (`127.0.0.1:10024`), không áp dụng xác thực mTLS hay token production.
