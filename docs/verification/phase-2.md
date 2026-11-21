# Ma trận truy vết Phase 2

| Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|
| Quán nhận nguyên liệu v1.1 | Headless đọc kho cá kèo, khách gọi cá kèo nướng và giữ đúng lượng theo công thức. | Đạt |
| Vòng ngày và tính tất định | Chạy cùng seed và đầu vào hai lần; so từng byte JSONL, kiểm kế hoạch ngày, thứ tự gather → quan → shop và kết thúc sau một ngày. | Đạt |
| Kiểm tham số số ngày | Từ chối 0, 6 và `--days` trong chế độ quán; mã thoát 2, không tạo file đầu ra. | Đạt |
| Pause/Resume và Shop | Chạy lại test tích hợp có sẵn cho đồng hồ, chuyển ngày, nâng cấp oxy và lỗi mua hàng. | Đạt |
| Hồi quy Phase 1 | Chạy smoke, luật gather và scenario quán; bổ sung kiểm thời lượng ca mặc định và nguyên nhân từ chối ID khách trùng. | Đạt — 43 test |

[Bằng chứng chạy test](../proof/phase-2/qa-tests.txt): 6 kiểm tra Phase 2 được chọn, 43 hồi quy Phase 1, 71 test toàn bộ đều đạt. Kết quả dựa trên nhánh triển khai day/shop/pause tại `e486b79` cùng các commit QA.

Phạm vi kiểm chứng Quán v1.1 ở đây là nhập kho, khách gọi món và giữ nguyên liệu. Chưa kiểm riêng toàn bộ hành trình nấu, phục vụ và thanh toán.
