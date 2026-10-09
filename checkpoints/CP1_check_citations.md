# HƯỚNG DẪN THỰC HIỆN CHECKPOINT 1: TRÌNH KIỂM TRA TRÍCH DẪN (check_citations.py)

---

## 1. Mục tiêu (Objectives)
- Xây dựng công cụ kiểm tra tính toàn vẹn và hợp lệ của các trích dẫn trong báo cáo khoa học dựa trên tệp dữ liệu nguồn (`sources.json`).
- Script này chạy **bên trong Sandbox** (môi trường cô lập của Daytona/Docker), do đó chỉ dùng thư viện chuẩn Python (`re`, `json`, `sys`, `urllib`...).
- Giúp hệ thống Agent có khả năng tự đánh giá (self-reflection/validation): nếu báo cáo vi phạm trích dẫn, script trả về mã lỗi (`exit 1`) và danh sách vấn đề cụ thể để Lead Agent đọc và sửa lại.

---

## 2. Yêu cầu chi tiết (Requirements & Rubric Alignment)

### 2.1 Điểm Rubric liên quan
- **Tiêu chí 4.1 (7 điểm)**: `python3 check_citations.py reports/<slug>.md reports/<slug>.sources.json` in `OK` cho tất cả các báo cáo. Lưu ý: Giảng viên sẽ kiểm tra lại bằng script chuẩn của giảng viên gồm đầy đủ 6 quy tắc; không được nới lỏng hay bỏ qua quy tắc nào.
- **Tiêu chí 3.1 (6 điểm)**: Tệp `check_citations.py` được nạp lên sandbox và agent chạy nó qua công cụ `execute`.

### 2.2 Các quy tắc kiểm tra bắt buộc (theo GUIDE.md Phần 4)
Hàm `check(report_text: str, sources: list) -> list[str]` phải trả về một danh sách các chuỗi mô tả lỗi (trả về list rỗng `[]` nếu hoàn toàn hợp lệ):

1. **Kiểm tra `sources` không rỗng**: Nếu `sources` rỗng (`len(sources) == 0`) hoặc không hợp lệ -> Báo lỗi `no sources in sources.json`.
2. **Kiểm tra từng mục trong `sources`**:
   - Trường `n` phải là số nguyên (`isinstance(s.get("n"), int)`).
   - Trường `url` phải bắt đầu bằng `http://` hoặc `https://`.
   - Không được có 2 nguồn trùng URL nhau (`duplicate URL`).
3. **Phân tách thân bài và References**:
   - Báo cáo bắt buộc phải chứa tiêu đề `## References` (sử dụng regex định dạng dòng tiêu đề `(?m)^##\s+References\s*$`).
   - Phần đứng trước tiêu đề là **Thân báo cáo (Body)**. Các trích dẫn số nằm sau tiêu đề `## References` không được tính là trích dẫn trong thân bài.
4. **Kiểm tra trích dẫn trong thân bài**:
   - Trích xuất toàn bộ các số `[n]` xuất hiện trong thân bài.
   - **Lưu ý loại trừ**: Không tính các `[n]` nằm trong khối code (` ```...``` ` hoặc ` `...` `) và không tính Markdown link dạng `[n](url)`.
   - **Xử lý dạng gộp**: Nếu có dạng `[1, 2]` hoặc `[1-3]`, cần tách/khai triển thành các số riêng biệt (1, 2 hoặc 1, 2, 3) để không bỏ sót trích dẫn.
   - **Hai chiều đối chiếu**:
     - Mọi số `n` được trích dẫn trong thân bài phải tồn tại trong `sources.json`. Nếu không -> Lỗi: `[n] cited but missing from sources.json`.
     - Mọi số `n` có trong `sources.json` phải được trích dẫn ít nhất 1 lần trong thân bài. Nếu không -> Lỗi: `source [n] never cited`.
5. **Kiểm tra cấu trúc mục `## References`**:
   - Lọc các dòng bắt đầu bằng `[n]` trong phần References.
   - Mỗi nguồn trong `sources` phải có **đúng 1 dòng tham khảo** tương ứng (không thiếu, không lặp lại số, không chứa số nằm ngoài `sources`).
6. **Kiểm tra URL trong dòng tham khảo**:
   - Mỗi dòng tham khảo phải chứa **đúng 1 HTTP/HTTPS URL**.
   - URL này phải trùng khớp chính xác với `url` của nguồn `n` trong `sources.json`.
   - Nghiêm cấm việc gộp nhiều nguồn dưới 1 số (ví dụ: `[3] Paper A; Paper B; Paper C...`).

---

## 3. Hướng dẫn thực hiện chi tiết (Step-by-Step Implementation)

### Bước 1: Loại bỏ khối code trước khi quét trích dẫn
Tránh quét nhầm các ký tự số trong khối lệnh hoặc ví dụ code:
```python
import re

def remove_code_blocks(text):
    # Xóa khối code nhiều dòng ```...``` và code inline `...`
    text_no_blocks = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text_clean = re.sub(r'`[^`\n]*`', '', text_no_blocks)
    return text_clean
```

### Bước 2: Tách Body và References
```python
ref_heading_match = list(re.finditer(r'(?m)^##[ \t]+References[ \t]*$', report_text))
if not ref_heading_match:
    problems.append("missing '## References' section")
    # Vẫn có thể tiếp tục phân tích hoặc return sớm tùy logic
```

### Bước 3: Tìm trích dẫn trong Body
Sử dụng regex tìm `\[(\d+(?:\s*[,–-]\s*\d+)*)\](?!\()` để lấy các cụm trích dẫn:
- Tách dấu phẩy `,` và dấu gạch nối `-` / `–` để lấy toàn bộ danh sách số nguyên `int`.
- Gom vào tập hợp `cited_in_body: set[int]`.

### Bước 4: Kiểm tra phần References
- Lấy các dòng từ sau tiêu đề `## References`.
- Với mỗi dòng có dạng `^\s*\[(\d+)\]\s*(.*)$`:
  - Trích xuất số tham khảo và URL trong dòng (dùng regex URL: `https?://[^\s)\]]+`).
  - Kiểm tra xem có đúng 1 URL không (`len(urls) == 1`).
  - So khớp với URL của nguồn tương ứng trong `sources.json`.

### Bước 5: Kiểm thử độc lập (Unit Test)
Tự tạo một file test nhanh hoặc chạy trực tiếp:
```bash
python check_citations.py reports/sample.md reports/sample.sources.json
```
Thử cố tình tạo các lỗi (thiếu URL, trích dẫn số 99 không có trong sources, gộp `[1, 2]`) để kiểm tra xem script có bắt chính xác lỗi không.

---

## 4. Kiến thức cần học được (Key Learnings & Takeaways)

1. **Deterministic Post-Validation trong Hệ thống AI**:
   - LLM thường có xu hướng "ảo giác" (hallucination) hoặc định dạng sai lệch khi viết danh sách tham khảo.
   - Việc dùng một validator viết bằng code thuần túy (không qua LLM) giúp bảo đảm tiêu chuẩn nghiêm ngặt và tính nhất quán tuyệt đối.
2. **Kỹ thuật Parsing Markdown bằng Regex**:
   - Phân biệt cú pháp trích dẫn số `[n]` với Markdown link `[n](url)` và mã nguồn `inline code`.
   - Kỹ thuật phân tách tài liệu dựa trên Markdown Headings.
3. **Môi trường Sandbox Execution**:
   - Viết mã không phụ thuộc vào thư viện bên ngoài (`third-party dependencies`) để có thể chạy mượt mà trong bất kỳ container tối giản nào (`python:3.12-slim`).
