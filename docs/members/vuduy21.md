# vuduy21 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:** Phụ trách `client/ui` và vai Scrum/Release. HUD gather/quan Phase 1 (`ef766b5`), kho khả dụng và nhận `hand` dạng chuỗi (`eba52be`), `--mode day` trong `live.py` với màn chờ, cửa hàng, tạm dừng (`c0228b8`, `68f8268`), kho cá thể và độ tươi (`8ea2229`), chế độ Tương phản cao + 3 cảnh báo (`93dd8a6`); thêm README, kế hoạch và ảnh proof cho từng phase.
- **Tôi đã review:** Đọc `quan.py` của Huy (`e4853a8`) và lập danh sách 9 điểm lệch PRD để báo Huy; đối chiếu nền v1.2 của Đạt (`fef6fc0`) với UI bằng snapshot thật.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI hiển thị thẳng `stock` làm "kho khả dụng", dù PRD mục D nói `stock` gồm cả phần giữ chỗ. Tôi phát hiện khi đối chiếu PRD và hỏi lại Huy, rồi sửa thành `stock` trừ `reserved`.
- **Điều tôi học được:** Cần chốt mẫu snapshot sớm và kiểm trên dữ liệu thật; ảnh chụp tĩnh không thay được việc chơi tay trọn vòng.
