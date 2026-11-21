# Credits

## Asset ngoài
Chưa dùng asset ngoài. Toàn bộ hình ảnh trong game (bến, cây dừa nước, cá, bông, nhà bè, đèn dây, Út Sen) được vẽ bằng mã trên `<canvas>` trong `chonoi/web/index.html`; chưa có âm thanh. Nhân vật và bối cảnh là bản gốc của lab.

Khi thêm asset: ghi nguồn, tác giả, giấy phép (chỉ CC0 / CC-BY / MIT hoặc tự tạo).

## Công cụ AI đã dùng
- Antigravity (Gemini): `sim/gather`, hợp đồng, vòng Ngày/cửa hàng, bench/soak, skill `phase-release-check` của Đạt.
- Antigravity (Gemini Flash) ở Phase 1, Claude Code (Opus 5.5) ở Phase 2–4: `sim/quan`, `docs/clarify.md`, README của Huy.
- Claude Code (Sonnet 5.5): UI/HUD, tài liệu của Duy.
- Codex: test hộp đen, hồi quy, bằng chứng và skill `qa-regression` của Đức Anh.

Mọi thay đổi do AI viết đều được người phụ trách module đọc lại và chạy test trước khi gộp.

Chi tiết theo người và phase: [docs/ai-usage-log.md](docs/ai-usage-log.md).
