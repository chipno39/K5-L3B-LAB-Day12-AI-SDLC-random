# Ma trận truy vết Phase 2

| Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|
| Quán nhận nguyên liệu v1.1 | Headless đọc kho cá kèo, khách gọi cá kèo nướng và giữ đúng lượng theo công thức. | Đạt |
| Phục vụ món cá kèo nướng | Dựng scenario có món trên tay, phục vụ đúng khách, kiểm tiền món và boa được cộng đúng một lần sau khi ăn xong. | Đạt |
| Vòng ngày và tính tất định | Chạy cùng seed và đầu vào hai lần; so từng byte JSONL, kiểm kế hoạch ngày, thứ tự gather → quan → shop và kết thúc sau một ngày. | Đạt |
| Kiểm tham số số ngày | Từ chối 0, 6 và `--days` trong chế độ quán; mã thoát 2, không tạo file đầu ra. | Đạt |
| Pause/Resume và Shop | Chạy lại test tích hợp có sẵn cho đồng hồ, chuyển ngày, nâng cấp oxy và lỗi mua hàng. | Đạt |
| Hồi quy Phase 1 | Chạy smoke, luật gather và scenario quán; bổ sung kiểm thời lượng ca mặc định và nguyên nhân từ chối ID khách trùng. | Đạt — 43 test |

[Bằng chứng chạy test](../proof/phase-2/qa-tests.txt): 7 kiểm tra Phase 2 được chọn, 43 hồi quy Phase 1, 72 test toàn bộ đều đạt. Kết quả dựa trên nền `origin/main` tại `ef358d1` cùng các commit QA.

Phạm vi kiểm chứng Quán v1.1 ở đây là nhập kho, khách gọi món và giữ nguyên liệu, phục vụ và thanh toán từ scenario có món sẵn. Chưa kiểm hành trình nấu món.

## Kiểm tra tích hợp đóng ca

Trên bản gộp tạm QA `1984552` với `feat/p2-quan` tại `70e5662`, khách đang ăn trả tiền, khách đang chờ rời đi không mất uy tín, và cả hai sự kiện có lý do `closing` trước `quan_end`. Quán trống vẫn chỉ phát `quan_end`.

[Bằng chứng chạy test](../proof/phase-2/quan-closing.txt): 3 test đóng ca, 43 test hồi quy Phase 1 và 82 test toàn bộ đều đạt trên bản gộp tạm.
