# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | `first_customer_tick` là tick mà khách xuất hiện sau khi giảm đồng hồ hay trước bước mô phỏng? Nếu đủ nguyên liệu cho nhiều món thì luật chọn món nào? | Chưa rõ; cần chốt trước khi viết test về lịch và chọn món. | PO / giảng viên |
| 2 | 2026-11-21 | Scenario khách `quan` được phép có những trạng thái/field nào và reservation nguyên liệu được tính ra sao? Khi nào fixture phải bị từ chối (ví dụ assigned thiếu món, eating thiếu giá/tip)? | Chưa rõ; cần chốt schema và invariant fixture. | PO / giảng viên |
| 3 | 2026-11-21 | Khi ca kết thúc cùng tick với món chín, khách hết kiên nhẫn, hoặc khách đang ăn, thứ tự event và kết quả thanh toán/khách rời là gì? | Chưa rõ; cần chốt thứ tự tick và hành vi đóng ca để test ổn định. | PO / giảng viên |
