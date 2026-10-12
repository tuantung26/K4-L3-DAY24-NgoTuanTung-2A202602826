# Verification — điền trước khi nộp

- OS / Python / Gitleaks version:
  - OS: Windows 11 (PowerShell)
  - Python: 3.12.8
  - Gitleaks: v8.30.1 (chưa cài trên máy — test supply chain vẫn pass vì test_supply_chain.py không gọi scanner trực tiếp, chỉ kiểm file .pre-commit-config.yaml, requirements.lock và secrets-incident.md)

- `python -m pytest tests/ -q`:
  ```
  .................................
  33 passed in 6.78s
  ```

- `pre-commit run --all-files`: Gitleaks chưa được cài trong PATH trên máy Windows (binary .exe chưa được tải về trước giờ lab). Kết quả: hook bị skip khi chạy `pre-commit run --all-files` vì không tìm thấy executable `gitleaks`. Để fix: tải `gitleaks_8.30.1_windows_x64.zip` từ https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1, giải nén và thêm vào PATH, sau đó chạy lại.

- Ledger verify:
  ```
  True
  ```
  Hash chain intact, mọi dòng có reason non-empty.

- Các lỗi còn lại:
  - **Gitleaks chưa trong PATH**: Checkpoint 4 (`pre-commit run --all-files`) cần cài Gitleaks v8.30.1 theo hướng dẫn README trước buổi lab. Test `test_supply_chain.py` PASS (3/3) vì các kiểm tra logic file đều hoàn chỉnh.
  - **Windows native**: Lab chạy trên Windows, không phải WSL2 Linux như khuyến nghị — các lệnh shell đã được điều chỉnh dùng PowerShell.
