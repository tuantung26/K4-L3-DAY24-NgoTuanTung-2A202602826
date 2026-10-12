# Secret giả trong lịch sử Git — điền trong checkpoint 4

- Scanner và phiên bản: Gitleaks v8.30.1
- Commit chứa token giả: `1bdd849` (commit `1bdd849922156c868a5ee9293d68f5b72e242d2c` - "chore: seed student lab with synthetic secret exercise")
- File, rule và kết quả quét lịch sử: File `lab-fake-secret.txt` tại commit `1bdd849`. Rule ID kích hoạt: `lab24-synthetic-token`. Quét lịch sử với `gitleaks git --config .gitleaks.toml` phát hiện 1 finding token giả (REDACTED theo --redact flag).
- Kết quả quét file hiện tại: File `lab-fake-secret.txt` đã được xóa ở commit tiếp theo. Quét file hiện tại với `gitleaks dir --config .gitleaks.toml .` cho kết quả sạch (0 findings).
- Nếu đây là credential thật, cần xử lý thế nào: Cần lập tức thu hồi / rotate secret ngay trên hệ thống cung cấp (Identity Provider / API backend / Vault), vô hiệu hóa token cũ, rà soát nhật ký truy cập (audit log) xem token đã bị lợi dụng trái phép chưa, và cấp phát credential mới thay thế.
- Vì sao xoá file khỏi HEAD hoặc pin dependency vẫn chưa đủ: Xóa file khỏi commit hiện tại (HEAD) không xóa được commit cũ trong lịch sử Git; bất kỳ ai clone repo với đầy đủ Git history đều có thể xem lại file qua `git log` hoặc `git show`. Pin dependency và hook chỉ có tác dụng ngăn chặn các lỗi phát sinh trong tương lai hoặc kiểm soát tính toàn vẹn của mã nguồn, chứ không thể làm mất hiệu lực một secret đã bị lộ ra ngoài. Do đó, việc rotate / thu hồi trực tiếp từ nguồn là bước bắt buộc và duy nhất đảm bảo an toàn.
