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

## Đồ họa cảnh quán (làm lại)
Người, bàn, bếp và món ăn được vẽ lại (chỉ là lớp hiển thị, vẽ từ snapshot; không đổi luật/headless):
- **Người** (Út Sen, khách): có đầu, tóc, mặt (mắt, miệng, má), áo bà ba, tay, chân, bóng. Út Sen buộc khăn rằn, bím tóc, đi/bưng món (chân đổi nhịp khi đi). Khách có dáng riêng suy ra từ id (áo, tóc, da, nón lá, khăn rằn); khi ăn thì há miệng, khi sắp giận thì cau mày đỏ má.
- **Bàn** gỗ tròn có vân, ống đũa, chén nước mắm, bảng số bàn. **Bếp** lò đất nung gạch, miệng lò có lửa bập bùng khi nấu, nồi, củi; món chín hiện đĩa món trên mặt bếp kèm dấu ✔.
- **Món ăn**: mỗi món một hình riêng (6 món) ở bong bóng gọi món, trên tay Út Sen, trên bàn khi khách ăn, trên bếp khi chín, và trong khung đơn / thực đơn.
- Vẽ theo độ sâu (xa → gần) nên Út Sen đi phía sau hoặc phía trước bàn đúng chỗ.

| Ảnh | Cho thấy |
|---|---|
| `quan-do-hoa-moi.png` / `...-tuong-phan-cao.png` | cảnh quán đông: bếp đang nấu + bếp chín, khách chờ / ăn / sắp giận, Út Sen bưng món |
| `quan-6-mon-an-co-hinh.png` | cả 6 món cùng lúc (bàn, bếp chín, bong bóng, thực đơn), phóng to |

Giới hạn trung thực: ảnh dựng từ snapshot đã chỉnh (đặt sẵn khách, bếp, món), chưa phải một lượt chơi thật liên tục; hình vẽ bằng mã nên là phong cách đơn giản, chưa phải đồ họa chuyên nghiệp.

## Đồ họa cảnh buổi sáng (làm lại)
Chỉ là lớp hiển thị, vẽ từ snapshot; không đổi luật/headless:
- **Út Sen**: dưới nước là người bơi nhìn nghiêng (kính lặn, khăn rằn buộc đầu, bím tóc bay, áo bà ba, tay bơi, chân đạp nước, giỏ lưới đeo hông), quay theo hướng bơi và lật khi quay trái để không bị lộn ngược; nhịp tay chân nhanh khi đang bơi, chậm khi đứng yên. Trên mặt nước thì nổi, chỉ thấy nửa người trên, có sóng gợn quanh người.
- **Bờ và bến**: bờ xa mờ có nhà sàn mái lá, bụi dừa nước, mây trôi; bến gỗ có ván, cột, đèn lồng, dây neo và ghe mái lá đậu cạnh (nhấp nhô theo sóng).
- **Dưới nước**: tia nắng xiên, đáy sông bùn có đá, rong đung đưa, phù sa lơ lửng.
- **Cây trên mặt nước**: bông súng (lá có khuyết, hoa hồng nhiều lớp), bông điên điển (cụm hoa vàng buông trên cành), kèo nèo (bụi cỏ nước đầu vàng).
- **Cá**: cá linh (bạc, thon, vạch bên, đuôi chẻ), cá kèo (đầu to, mắt lồi, vây ngực cam, thân đốm nâu) có hình riêng, cũng dùng trong ô giỏ.

| Ảnh | Cho thấy |
|---|---|
| `sang-noi-tren-mat-nuoc-ben-ghe.png` | Út Sen nổi cạnh bông điên điển, bến + ghe + đèn lồng, bờ xa, bông, cá, Cá Sấu |
| `sang-ut-sen-boi-duoi-nuoc.png` / `...-tuong-phan-cao.png` | Út Sen đang bơi chéo xuống dưới nước (thường và tương phản cao) |

Giới hạn trung thực: ảnh dựng từ snapshot đã chỉnh (đặt sẵn vị trí, vận tốc, hướng), chưa phải một lượt chơi liên tục; Út Sen vẫn khá nhỏ trên cửa sổ hẹp vì cả dòng sông dài 100 m phải vừa một màn hình.
