# Ma trận truy vết Phase 4

Nền kiểm chứng Contract v1.3: `771e17f`.

| Yêu cầu | Cách kiểm chứng | Kết quả |
|---|---|---|
| Hồi quy P1–P3 | Chạy toàn bộ unittest trên v1.3. [Log](../proof/phase-4/qa-v13-regression.txt) | Đạt: 108 test, gồm cả kiểm tra bench và soak. [Nền v1.2](../proof/phase-4/regression.txt): 106 test đạt. |
| `bench_cmd` | Chạy lệnh trong contract với seed 1, làm nóng 3 giây và đo 30 giây. Xác nhận kích thước 1280×720 trong mã và đủ 5 trường JSON. [Kết quả](../proof/phase-4/qa-bench.json) | Đạt kiểm tra lệnh và báo cáo. FPS đo bước dựng lệnh vẽ trong Python; đây là phạm vi của số liệu benchmark. |
| `soak_cmd` | Chạy hai lần với seed 1, mỗi lần 10 ngày; so kết quả sau khi bỏ thời gian chạy thực. [Lần 1](../proof/phase-4/qa-soak-1.json), [lần 2](../proof/phase-4/qa-soak-2.json) | Đạt: kết quả từng ngày khớp, đủ ngày 1–10 và `crashes=0` cả hai lần. |

[Lệnh và kết quả kiểm tra](../proof/phase-4/qa-commands.txt).
