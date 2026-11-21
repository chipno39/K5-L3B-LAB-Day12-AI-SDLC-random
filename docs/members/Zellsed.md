# Zellsed (Quách Ngọc Huy) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đóng vai trò Product Owner (PO), chủ trì làm rõ các điểm mơ hồ về luật Mở Quán trong [docs/clarify.md](../clarify.md).
  - Trực tiếp phát triển toàn bộ logic mô phỏng buổi tối (`sim/quan`) gồm Lát 3 (quản lý khách đến theo lịch, kho khả dụng, giữ chỗ `reserved`, xử lý kiên nhẫn và `no_dish`) và Lát 4 (tương tác bếp/bàn theo đúng thứ tự ưu tiên, nấu món, bưng phục vụ, tính tiền và tiền boa $20\%$) trong [chonoi/sim/quan.py](../../chonoi/sim/quan.py).
- **Tôi đã review (kèm link):**
  - Review hợp đồng tích hợp [docs/contracts/README.md](../contracts/README.md) của Integrator (Đạt) để đồng bộ hóa 100% schema sự kiện và snapshot khách hàng.
  - Kiểm tra chéo logic `sim/gather` (phần dự phòng).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu đặt tên trường trong sự kiện là `customer_id` thay vì `order_id` như bản hợp đồng tích hợp v1.0 đã thống nhất; tôi phát hiện qua việc đọc kỹ `docs/contracts/README.md` và sửa lại code để đảm bảo tương thích hoàn toàn.
- **Điều tôi học được:**
  - Thiết lập ranh giới sở hữu file rõ ràng ngay từ kickoff giúp cả nhóm code song song mà không hề bị xung đột merge.
