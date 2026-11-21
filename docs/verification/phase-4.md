# Ma trận truy vết Phase 4

| Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|
| Hồi quy P1–P3 | Chạy toàn bộ unittest trên nền `2e20545`. [Log](../proof/phase-4/regression.txt) | Đạt trên nền v1.2: 106 test. Chạy lại trên bản phát hành v1.3. |
| `bench_cmd` | Chạy lệnh khai trong contract, lưu `bench.json`, đối chiếu cảnh 1280×720, làm nóng 3 giây và đo 30 giây với tiêu chí Phase 4. | Chờ lệnh v1.3. |
| `soak_cmd` | Chạy đủ 10 ngày hai lần với cùng seed và đầu vào. So kết quả mô phỏng, xác nhận đủ 10 ngày và `crashes=0` ở cả hai lần. | Chờ lệnh v1.3. |
