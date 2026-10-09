# HƯỚNG DẪN THỰC HIỆN CHECKPOINT 2: BỘ CÔNG CỤ NGUỒN DỮ LIỆU & RETRY (tools.py)

---

## 1. Mục tiêu (Objectives)
- Xây dựng 5 công cụ tìm kiếm dữ liệu học thuật và thông tin trên web chạy ở phía **HOST**:
  1. `arxiv_search`: Tìm kiếm bài báo trên arXiv.
  2. `hf_daily_papers`: Lấy các bài báo thịnh hành (Daily Papers) trên Hugging Face.
  3. `hf_search_papers`: Tìm kiếm bài báo theo chủ đề trên Hugging Face.
  4. `web_search`: Tìm kiếm trang web qua giao thức MCP của Exa.
  5. `web_fetch`: Đọc nội dung chi tiết một URL dưới dạng Markdown.
- Xây dựng cơ chế **`with_retry`** tự động xử lý lỗi mạng tạm thời, lỗi giới hạn tốc độ (Rate Limit / HTTP 429), HTTP 5xx với cơ chế Exponential Backoff, Jitter ngẫu nhiên và tôn trọng header `Retry-After`.
- Đảm bảo tính bền vững: Mọi công cụ phải trả về chuỗi văn bản (JSON compact string hoặc "NO RESULTS" / "ERROR: ...") và **tuyệt đối không để crash / ném exception ra ngoài**.

---

## 2. Yêu cầu chi tiết (Requirements & Rubric Alignment)

### 2.1 Điểm Rubric liên quan (Tổng cộng 20 điểm - Phần 1)
- **Tiêu chí 1.1 `with_retry` (6 điểm)**:
  - Backoff lũy thừa: `delay = min(cap, base * 2**attempt) + jitter`.
  - Tôn trọng header `Retry-After` nếu server phản hồi.
  - Chặn trên bằng `cap`.
  - Lần thử cuối thất bại thì ném lại lỗi, không ngủ thêm.
  - Chỉ retry các lỗi tạm thời (`RetryableError`, HTTP 429, 500, 502, 503, 504, `httpx.TransportError`). Không retry lỗi lập trình hoặc HTTP 400, 401, 404.
- **Tiêu chí 1.2 Năm công cụ (8 điểm)**:
  - Đủ 5 công cụ chuẩn interface, trả về đúng định dạng bản ghi theo `GUIDE.md`.
  - Rỗng -> trả về chuỗi `"NO RESULTS"`.
  - Hỏng -> trả về chuỗi `"ERROR: <loại_lỗi>: <thông_điệp>"`.
  - Không bao giờ ném Exception (mỗi công cụ ném lỗi trừ 1.6đ).
- **Tiêu chí 1.3 Exa Rate Limit & Bảo mật Key (3 điểm)**:
  - Phát hiện rate limit của Exa (bản miễn phí trả về HTTP 200 kèm cờ trong `result._meta` hoặc thông báo trong text) và trigger retry.
  - Che giấu khóa `EXA_API_KEY`: Khóa không bao giờ được xuất hiện trong chuỗi báo lỗi trả về cho Agent.
- **Tiêu chí 1.4 arXiv Etiquette & Sanitization (3 điểm)**:
  - Gọi qua HTTPS (`https://export.arxiv.org/api/query`).
  - Đảm bảo giãn cách ít nhất 3 giây giữa hai lần gọi API.
  - Làm sạch câu truy vấn: chỉ giữ chữ, số, dấu gạch nối để tránh hỏng cú pháp truy vấn arXiv.

---

## 3. Hướng dẫn thực hiện chi tiết (Step-by-Step Implementation)

### 3.1 Cài đặt `with_retry` (TODO 1)
```python
import random
import time
import httpx

def with_retry(fn, *, attempts=5, base=1.0, cap=30.0):
    for attempt in range(attempts):
        try:
            return fn()
        except (RetryableError, httpx.TransportError, httpx.HTTPStatusError) as e:
            if attempt == attempts - 1:
                raise
            # Xác định thời gian chờ (delay)
            retry_after = getattr(e, 'retry_after', None)
            if retry_after is not None:
                delay = float(retry_after)
            else:
                # Exponential backoff + jitter ngẫu nhiên
                delay = min(cap, base * (2 ** attempt)) + random.uniform(0.1, 0.5)
            time.sleep(min(cap, delay))
```
*Mẹo phụ*: Viết hàm bọc helper để phân loại status code: HTTP 429, 500..504 ném `RetryableError`.

### 3.2 Cài đặt `arxiv_search` (TODO 2)
1. **Làm sạch query**: Sử dụng regex loại bỏ ký tự lạ `re.findall(r'[\w\-]+', query)`. Nếu rỗng, trả về `"NO RESULTS"`.
2. **Rate Limit 3s**: Sử dụng biến toàn cục lưu thời điểm gọi gần nhất `_LAST_ARXIV_CALL = 0`. Nếu `time.time() - _LAST_ARXIV_CALL < 3.0`, tính toán thời gian cần ngủ thêm trước khi gửi request.
3. **Parse Atom XML**:
   - Sử dụng `xml.etree.ElementTree` với namespace `ns = {'atom': 'http://www.w3.org/2005/Atom'}`.
   - Chuẩn hóa ID: Cắt bỏ tiền tố URL và phiên bản `vN` (ví dụ: `2501.00001v1` -> `2501.00001`).
   - URL chuẩn: `https://arxiv.org/abs/<id>`.
   - Cắt ngắn `summary` khoảng 600 ký tự và dọn sạch dấu xuống dòng thừa.

### 3.3 Cài đặt `hf_daily_papers` & `hf_search_papers` (TODO 3)
1. **Daily Papers**:
   - Endpoint: `https://huggingface.co/api/daily_papers`.
   - Trả về danh sách paper với các trường: `id`, `url` (`https://huggingface.co/papers/<id>`), `published`, `title`, `summary`, `upvotes`, `github`, `stars`.
   - Nếu có tham số `keyword`: Lọc case-insensitive trong `title` và `summary`. Sắp xếp giảm dần theo `upvotes`.
2. **Search Papers**:
   - Endpoint: `https://huggingface.co/api/papers/search?q=<query>&limit=<limit>`.
   - Ưu tiên trường `ai_summary` nếu có, nếu không lấy `summary`. Cắt gọn khoảng 600 ký tự.

### 3.4 Cài đặt Exa MCP `web_search` & `web_fetch` (TODO 4)
1. **Giao thức MCP qua HTTP POST**:
   - URL: `https://mcp.exa.ai/mcp` (hoặc `https://mcp.exa.ai/mcp?exaApiKey=...` nếu có key).
   - Headers: `Content-Type: application/json`, `Accept: application/json, text/event-stream`.
   - Payload JSON-RPC 2.0:
     ```json
     {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "web_search_exa", "arguments": {"query": "...", "objective": "...", "numResults": 5}}}
     ```
2. **Bắt Rate Limit ẩn của Exa**:
   - Đọc kết quả SSE (các dòng bắt đầu bằng `data:`).
   - Kiểm tra `result.get("_meta")` hoặc nội dung trả về có chứa từ khóa cảnh báo rate limit. Nếu gặp -> ném `RetryableError` với delay phù hợp.
3. **Bảo mật API Key**:
   - Khi bắt Exception, nếu chuỗi lỗi có chứa `os.getenv("EXA_API_KEY")`, thay thế chuỗi key thành `[REDACTED]` trước khi trả về chuỗi `ERROR: ...`.

### 3.5 Kiểm thử độc lập
Chạy trực tiếp file `tools.py`:
```bash
python tools.py
```
Kiểm tra cả 5 công cụ in ra kết quả JSON hợp lệ, không ném lỗi ra terminal.

---

## 4. Kiến thức cần học được (Key Learnings & Takeaways)

1. **Host vs Sandbox Security Model**:
   - Tại sao các công cụ mạng và API key phải chạy ở Host? Để ngăn chặn Prompt Injection bên trong Sandbox đánh cắp thông tin hoặc phát tán mã độc ra ngoài mạng.
2. **Khả năng phục hồi dịch vụ mạng (Resilience & Rate Limiting)**:
   - Hiểu sâu về hiện tượng Thundering Herd và vì sao phải thêm Jitter vào Exponential Backoff.
   - Nhận biết các dạng Rate Limiting tinh vi (không trả 429 mà trả HTTP 200 kèm cờ metadata).
3. **Chuẩn hóa dữ liệu đầu vào cho LLM (Context Window Management)**:
   - Tránh nhồi nhét nội dung web khổng lồ vào LLM context (cắt ngắn 600 ký tự cho tóm tắt paper, 12000 ký tự cho web fetch) giúp tiết kiệm token và tăng độ tập trung của Agent.
