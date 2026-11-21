# Ma trận truy vết Phase 3

| Yêu cầu | Cách kiểm chứng | Kết quả trên nền v1.2 |
|---|---|---|
| Kho file đếm v1.1 bị từ chối | Headless nhận file đếm cũ, thoát 2 và không tạo đầu ra. | Đạt |
| Giỏ Gather chỉ ươn khi dưới 30 | `test_gather_p3`: bắt đầu ở 30, qua ngưỡng mới phát `spoiled`, đúng một lần. | Đạt |
| Kho Quán hao tươi và giữ lại khi ươn | `test_qa_p3`: kiểm sự kiện, chọn ID thấp hơn khi hai món thay thế tươi bằng nhau, và `unfulfillable` khi hết hàng thay. | Chờ tích hợp Quán v1.2 |
| Chốt giá khi nấu | `test_qa_p3`: kiểm danh sách cá thể và giá làm tròn xuống theo độ tươi trung bình. | Chờ tích hợp Quán v1.2 |
| Hồi quy Phase 1–2 | Đổi fixture map đếm sang cá thể vì contract v1.2, giữ kiểm tra chuyển kho, nhận món và kết thúc ca. | Chưa đạt toàn bộ trên nền hiện tại |

Nền kiểm chứng: `fef6fc0` + QA `c035bdd`. [Kiểm tra nền](../proof/phase-3/foundation.txt): 19 test đạt. [Chạy toàn bộ](../proof/phase-3/full-suite.txt): 95 test, 5 failures và 10 errors. Nhánh nền còn dùng Quán v1.1, lỗi khi nhận kho cá thể. Cần chạy lại sau khi tích hợp Quán v1.2.
