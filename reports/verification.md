# Verification — điền trước khi nộp

- OS / Python / Gitleaks version:
  - OS: Windows 11 (PowerShell)
  - Python: 3.12.8
  - Gitleaks: v8.30.1 (binary tại `C:\Users\Hi\Downloads\gitleaks_8.30.1_windows_x64\gitleaks.exe`)

- `python -m pytest tests/ -q`:
  ```
  .................................
  33 passed in 6.78s
  ```

- `pre-commit run --all-files`:
  ```
  Detect hardcoded secrets.................................................Passed
  ```
  Quét file hiện tại (dir scan): **0 leaks found** (`gitleaks dir --config .gitleaks.toml .` → exit 0).
  Quét lịch sử (git scan): **2 findings** — đúng dự kiến:
    1. `1bdd849`: token giả gốc trong `lab-fake-secret.txt` (commit seed của lab).
    2. `1be1172`: nguyên văn token giả trong `reports/secrets-incident.md` (đã xóa ở HEAD, bằng chứng cho thấy xóa khỏi HEAD không xóa được git history).

- Ledger verify:
  ```
  True
  ```
  Hash chain intact, mọi dòng có reason non-empty.

- Các lỗi còn lại: Không có lỗi còn lại. Mọi test pass, pre-commit hook Passed, ledger verify True, attack-after.log rỗng (0 bytes).

