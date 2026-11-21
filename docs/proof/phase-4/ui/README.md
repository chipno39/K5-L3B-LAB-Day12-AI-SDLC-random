# Bằng chứng UI Phase 4 (TV 3 — Duy): Tương phản cao + 3 cảnh báo

**Bật/tắt chế độ Tương phản cao:** phím **H** (ở mọi màn, nhớ lựa chọn trong trình duyệt), hoặc mở `http://127.0.0.1:8000/?hc=1`. Chỉ là lớp hiển thị: không gửi gì vào sim, không đổi headless.

Tương phản cao làm gì: nền đen, khung viền trắng dày, chữ trắng/đen thay cho tông nâu nhạt, thanh có viền trắng, viền sáng quanh Út Sen / cá / Cá Sấu, ô giỏ trống có viền, **thanh kiên nhẫn có thêm số giây**, tăng độ tương phản và độ bão hòa toàn cảnh.

## Ba cảnh báo — luôn có CHỮ + biểu tượng ⚠ (không chỉ dựa vào màu), ở cả hai chế độ
| Cảnh báo | Điều kiện (đọc từ snapshot) | Hiển thị |
|---|---|---|
| Thủy quái gần | khoảng cách tới Cá Sấu ≤ 1.3 × `detect_radius` (chưa đuổi): "⚠ Thủy quái gần đây!" (cam); đang đuổi (`state: chase`): "⚠ THỦY QUÁI! Bơi lên mau!" (đỏ, nhấp nháy) | biểu ngữ + vòng phát hiện + vạch "vùng thủy quái" |
| Oxy sắp hết | dưới nước và oxy < 25%: "⚠ Sắp hết hơi — nổi lên"; oxy = 0: "⚠ HẾT HƠI! Nổi lên ngay!" (nhấp nháy) | biểu ngữ + thanh oxy có số giây + thanh đếm ngạt |
| Khách sắp giận | kiên nhẫn còn < 25% và chưa nhận món: "⚠ Khách T1 sắp giận! Phục vụ ngay" | biểu ngữ + dấu "!" đỏ nhấp nháy cạnh khách + chữ "sắp giận!" (HC: thêm số giây) |

| Ảnh | Tình huống |
|---|---|
| `canh-bao-thuy-quai-het-hoi-thuong.png` / `...-tuong-phan-cao.png` | gather: Cá Sấu đang đuổi + oxy = 0 (ảnh gốc ở `snapshots_canh_bao.json` #1) |
| `canh-bao-khach-sap-gian-thuong.png` / `...-tuong-phan-cao.png` | quan: khách T1 sắp hết kiên nhẫn, T3 còn nhiều (`snapshots_canh_bao.json` #3) |
| `menu-tuong-phan-cao.png` | menu chính ở chế độ tương phản cao, có dòng "H: chế độ tương phản cao (đang BẬT/tắt)" |

Cách tạo: `snapshots_canh_bao.json` suy ra từ snapshot gather v1.2 và quan v1.2 THẬT (`LiveGame`, `--mode day`), chỉnh vị trí/oxy/kiên nhẫn để gây cảnh báo; chụp bằng Edge headless qua một máy chủ tĩnh trả snapshot ở `/state`; `harness.js` chạy script `index.html` với canvas giả (`HC=1` để bật tương phản cao) → không lỗi runtime ở cả hai chế độ trên mọi bộ snapshot Phase 1–4.

Giới hạn trung thực:
- Ảnh là trạng thái tĩnh từ snapshot đã chỉnh, chưa phải một lượt chơi thật có cả ba cảnh báo kích hoạt tự nhiên; chưa gõ phím `H` trực tiếp trong trình duyệt (đã kiểm `?hc=1` và logic bật/tắt qua harness).
- "Tương phản cao" ở đây là lớp hiển thị tự làm, chưa đo bằng công cụ chuẩn (ví dụ tỉ lệ WCAG) cho từng màu.
- Chế độ không gồm phụ đề/âm thanh (game chưa có âm thanh).
