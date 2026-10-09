# HƯỚNG DẪN THỰC HIỆN CHECKPOINT 6: THẨM ĐỊNH TOÀN DIỆN & NỘP BÀI (self_check.py)

---

## 1. Mục tiêu (Objectives)
- Tiến hành thẩm định tự động toàn bộ sản phẩm bằng `self_check.py` trước khi nộp bài để phát hiện sớm mọi vi phạm rubric (thiếu báo cáo, thiếu subagent calls, thiếu họ nguồn, lỗi trích dẫn, lộ lọt API key).
- Rà soát an toàn thông tin (Secret Hygiene): Đảm bảo tệp `.env` không bị theo dõi bởi Git và không có chuỗi khóa bí mật nào lọt vào lịch sử commit.
- Hoàn thiện tài liệu dự án (`README.md`), mã nguồn sạch sẽ, không sửa các tệp lõi có sẵn, đẩy lên GitHub Repository công khai (Public Repo).

---

## 2. Yêu cầu chi tiết (Requirements & Rubric Alignment)

### 2.1 Điểm Rubric liên quan (Tổng cộng 10 điểm - Phần 6)
- **Tiêu chí 6.1 Không lộ bí mật (3 điểm)**:
  - Tệp `.env` phải nằm trong `.gitignore` và không bị Git theo dõi.
  - Không có chuỗi khóa API nào trong toàn bộ lịch sử Git (`git log`).
  - *Cảnh báo nghiêm khắc*: Lộ khóa bí mật sẽ bị **0 điểm toàn bộ Phần 6**.
- **Tiêu chí 6.2 Tài liệu README (3 điểm)**:
  - Tệp `README.md` của repo nêu rõ: Yêu cầu môi trường, cách cài đặt dependencies, cách cấu hình `.env`, cách chạy hệ thống với các chủ đề, cấu trúc các tệp kết quả trong thư mục `reports/`.
- **Tiêu chí 6.3 Mã sạch và tính toàn vẹn (2 điểm)**:
  - Mã nguồn trong các tệp tự viết (`tools.py`, `agents.py`, `research.py`, `check_citations.py`) dễ đọc, có chú thích, không có mã chết (`dead code`).
  - **Tuyệt đối không sửa các tệp CÓ SẴN**: `model.py` và `sandbox.py`. Giảng viên sẽ dùng bản gốc của hai tệp này để chấm.
- **Tiêu chí 6.4 `requirements.txt` (2 điểm)**:
  - Khai báo đầy đủ các thư viện để một người khác có thể tạo môi trường ảo và chạy thành công mà không gặp lỗi thiếu package.

---

## 3. Hướng dẫn thực hiện chi tiết (Step-by-Step Implementation)

### 3.1 Chạy công cụ tự kiểm tra `self_check.py`
Chạy lệnh kiểm tra tự động (lệnh này chỉ đọc file cục bộ, không tốn token LLM, không cần mạng):
```bash
python self_check.py
```

**Mục tiêu đầu ra lý tưởng**:
```text
topic                                                        result
survey about world model                                     OK
survey about reinforcement learning for LLM reasoning        OK
survey about LLM agents and tool use                         OK
survey about video and multimodal generation                 OK
survey about efficient inference and small language models   OK
git / secrets                                                OK

READY to submit (the manual parts of RUBRIC.md are still graded by a person).
```

Nếu có bất kỳ dòng nào báo `PROBLEMS`:
- Đọc kỹ thông báo lỗi chi tiết bên dưới.
- Nếu lỗi trích dẫn -> kiểm tra lại `check_citations.py` hoặc xem báo cáo có vi phạm quy tắc nào không.
- Nếu lỗi thiếu họ nguồn hoặc số lần subagent -> Chạy lại đề tài đó với prompt tối ưu hơn.
- Nếu lỗi git/secrets -> Thực hiện ngay bước 3.2 dưới đây.

### 3.2 Xử lý an toàn bảo mật (Git & Secrets)
1. **Kiểm tra trạng thái tệp `.env`**:
   ```bash
   git status
   ```
   Nếu thấy `.env` nằm trong danh sách "Changes to be committed" hoặc "Untracked files", kiểm tra lại `.gitignore`.
2. **Gỡ bỏ `.env` nếu lỡ add vào git**:
   ```bash
   git rm --cached .env
   ```
3. **Quét tìm API Key trong mã nguồn và Git History**:
   ```bash
   git log -p | grep -E "(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z-_]{35})"
   ```
   *Lưu ý*: Nếu đã lỡ commit API key thật lên Git: Bạn **bắt buộc phải vào trang quản lý của nhà cung cấp để REVOKE (hủy) ngay khóa đó**, sau đó reset lại commit.

### 3.3 Cập nhật `README.md`
Bổ sung hướng dẫn ngắn gọn cho người chấm:
- Hướng dẫn clone và cài đặt môi trường (`python -m venv .venv`, `pip install -r requirements.txt`).
- Hướng dẫn cấu hình API Keys (sao chép `.env.example` thành `.env`).
- Hướng dẫn tái hiện kết quả: `python research.py "<topic>"`.
- Hướng dẫn kiểm tra báo cáo: `python check_citations.py reports/<slug>.md reports/<slug>.sources.json`.
- Hướng dẫn tự kiểm tra: `python self_check.py`.

### 3.4 Commit và Đẩy lên Public GitHub Repo
```bash
git add check_citations.py tools.py agents.py research.py reports/ checkpoints/ README.md
git commit -m "feat: complete deep research multi-agent system and 5 survey reports"
git push origin main
```
Đảm bảo Repository trên GitHub được đặt ở chế độ **Public** để người chấm có thể truy cập.

---

## 4. Kiến thức cần học được (Key Learnings & Takeaways)

1. **Văn hóa Bảo mật DevSecOps & Bí mật mã nguồn**:
   - Thói quen tách biệt hoàn toàn giữa cấu hình nhạy cảm (`.env`) và mã nguồn mã hóa (`code base`).
   - Kỹ năng sử dụng các công cụ linter/pre-commit check để tự động ngăn chặn rò rỉ khóa bí mật.
2. **Quy trình Tự động hóa Đánh giá (Automated Self-Assessment)**:
   - Hiểu cách xây dựng các kịch bản kiểm thử tĩnh (Static Verification Scripts) để đối chiếu trực tiếp với tiêu chí đánh giá (Rubric) trước khi bàn giao sản phẩm.
3. **Tiêu chuẩn đóng gói sản phẩm phần mềm (Reproducibility)**:
   - Đảm bảo tính khả lặp (Reproducibility): Bất kỳ kỹ sư nào cũng có thể clone repo, cài đặt dependencies từ `requirements.txt`, và chạy lại đúng hành vi mà không gặp lỗi môi trường.
