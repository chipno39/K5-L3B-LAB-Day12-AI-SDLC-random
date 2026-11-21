# ldlda — phản tư cá nhân

- Tôi viết kiểm thử hộp đen cho Quán và vòng ngày, tạo skill `qa-regression`, rồi cập nhật fixture sang kho cá thể v1.2. [QA Phase 2](https://github.com/chipno39/K5-L3B-LAB-Day12-AI-SDLC-random/pull/7), [QA Phase 3](https://github.com/chipno39/K5-L3B-LAB-Day12-AI-SDLC-random/pull/10).
- Tôi rà lại tình huống đóng ca: khách đang ăn trả tiền, khách đang chờ rời đi và quán trống vẫn kết thúc đúng. [Bằng chứng đóng ca](../proof/phase-2/quan-closing.txt).
- Codex từng dùng giá trị độ tươi làm tròn của JSONL để so với snapshot Shop trong bộ nhớ. Lần chạy tích hợp báo lệch; tôi sửa kỳ vọng để giữ độ chính xác tại lớp đang kiểm thử.
- Tôi học được rằng bằng chứng cần ghi commit đã chạy và phạm vi kiểm tra. Khi hợp đồng đổi, cần tách lỗi do fixture cũ khỏi lỗi của hành vi trò chơi.
