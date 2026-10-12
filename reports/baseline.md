# Baseline — điền trong checkpoint 1

1. Agent có identity mỗi run chưa? Dẫn file/hàm:
Chưa có. Trong `agent/loop.py:27` (`_naive_loop`), hàm nhận trực tiếp `message` và `llm`, không sinh ra `run_id`, không gán `agent_id`, và không mang thông tin danh tính (identity hay principal/on_behalf_of) cho từng lượt chạy.

2. Ai cho phép `http_post`? Dẫn file/hàm:
Không có cơ chế/chính sách nào cấp phép hoặc kiểm duyệt. Trong `agent/loop.py:44` (`_naive_loop`), `tools.http_post` được gọi trực tiếp vô điều kiện khi `injected is not None` và có dữ liệu `collected`. Bản thân hàm `tools.http_post` (`agent/tools.py:68`) chỉ kiểm tra hard-coded allowlist địa chỉ IP/port (`127.0.0.1:10024`), hoàn toàn thiếu lớp Policy Enforcement Point (PEP) để kiểm tra quyền của principal hay phân loại dữ liệu (classification).

3. Nếu gửi sai PII ra sink, bằng chứng ở đâu? Dẫn file/hàm:
Bằng chứng nằm ở file log của mock sink tại `reports/sink.log` (được ghi bởi `sink/sink.py:46-47` trong `Handler.do_POST`), lưu lại toàn bộ body request POST chứa các bản ghi PII khách hàng dạng JSON. Ở phía agent, hoàn toàn không có audit ledger hay bằng chứng ghi vết nào được lưu lại.
