# HƯỚNG DẪN THỰC HIỆN CHECKPOINT 4: TÍCH HỢP HỆ THỐNG & ĐIỀU PHỐI SANDBOX (research.py)

---

## 1. Mục tiêu (Objectives)
- Xây dựng điểm khởi chạy chính của hệ thống (`research.py`): Điều phối toàn bộ quy trình từ khởi tạo Sandbox, nạp công cụ kiểm tra, cấu hình Agent, chạy quy trình nghiên cứu, đến việc xuất báo cáo và siêu dữ liệu (metadata).
- Quản lý vòng đời Sandbox (Daytona Cloud Sandbox hoặc Docker cục bộ) an toàn tuyệt đối: Luôn dọn dẹp và xóa Sandbox sau khi kết thúc chương trình (kể cả khi gặp lỗi ngoại lệ).
- Xử lý và ghi nhận đầy đủ siêu dữ liệu (`<slug>.meta.json`) làm bằng chứng chấm điểm tự động.

---

## 2. Yêu cầu chi tiết (Requirements & Rubric Alignment)

### 2.1 Điểm Rubric liên quan (Tổng cộng 10 điểm - Phần 3)
- **Tiêu chí 3.1 Dùng Sandbox thật (6 điểm)**:
  - Nạp tệp `check_citations.py` và `finalize_citations.py` lên Sandbox qua hàm `upload`.
  - Lead Agent thực thi kiểm tra bằng công cụ shell `execute`.
  - Kết quả báo cáo (`report.md`) và danh sách nguồn (`sources.json`) được tạo trong Sandbox và tải về máy host bằng hàm `download`.
- **Tiêu chí 3.2 Dọn dẹp và Bí mật (4 điểm)**:
  - Sử dụng cấu trúc `with open_sandbox() as backend:` để luôn đảm bảo giải phóng tài nguyên.
  - Tuyệt đối không tải `.env` hay API key lên Sandbox.
  - Nếu lần chạy thất bại (không có báo cáo, báo cáo rỗng hoặc `sources.json` lỗi) -> Thoát với mã lỗi khác 0 và **không được ghi đè hay để lại báo cáo rỗng**.

---

## 3. Hướng dẫn thực hiện chi tiết (Step-by-Step Implementation)

### 3.1 Cài đặt `slugify(topic)` (TODO 1)
Biến chủ đề người dùng nhập thành tên tệp an toàn, tránh tấn công Path Traversal:
```python
import re

def slugify(topic: str) -> str:
    # Chuyển chữ thường, thay các ký tự không phải chữ/số thành dấu gạch nối "-"
    s = re.sub(r'[^a-zA-Z0-9]+', '-', topic.strip().lower()).strip('-')
    # Cắt tối đa 60 ký tự, nếu chuỗi rỗng trả về fallback "topic"
    s = s[:60].strip('-')
    return s if s else "topic"
```

### 3.2 Cài đặt `build_prompt(topic)` (TODO 2)
Tạo câu lệnh (User message) rõ ràng, hướng dẫn Agent bắt đầu nghiên cứu sâu:
```python
def build_prompt(topic: str) -> str:
    return (
        f"Conduct a comprehensive, deep research survey on the topic: '{topic}'.\n\n"
        f"Follow your system instructions strictly:\n"
        f"1. Plan with `write_todos` and split the topic into at least 3 distinct sub-questions.\n"
        f"2. Delegate sub-questions to `researcher` subagents in parallel using the `task` tool.\n"
        f"3. Gather notes in `/tmp/work/research/notes/`.\n"
        f"4. Merge notes into `/tmp/work/research/sources.json` with >= 3 source families (arxiv, hf-daily, hf-search, web).\n"
        f"5. Write the body of the report to `/tmp/work/report/report.md` (Do NOT hand-write `## References`).\n"
        f"6. Run `/tmp/work/research/finalize_citations.py` using `execute`.\n"
        f"7. Run `/tmp/work/research/check_citations.py` using `execute` until it prints OK.\n"
        f"8. Perform a spot-check with `citation-checker` subagent.\n"
    )
```

### 3.3 Cài đặt `summarize(messages, elapsed, model_name)` (TODO 3)
Thu thập các số liệu thống kê từ lịch sử tin nhắn của Lead Agent:
- Đếm số lượt gọi các công cụ trong thuộc tính `tool_calls` của tin nhắn:
  - `subagent_calls`: Số lần gọi công cụ `task`.
  - `tool_calls`: Thống kê tần suất từng tool (e.g., `execute`, `read_file`, `write_file`, `task`...).
- Thu thập token tiêu thụ từ `usage_metadata` (nếu mô hình trả về): `tokens: {"input": total_in, "output": total_out}`.
- Làm tròn thời gian chạy: `elapsed_s = round(elapsed, 1)`.

### 3.4 Cài đặt `save_outputs(...)` (TODO 4)
Tải kết quả từ Sandbox và lưu thành 3 tệp trong thư mục `reports/`:
1. Dùng `download(backend, [REPORT_PATH, SOURCES_PATH])`.
2. Kiểm tra tính hợp lệ:
   - Nếu `report.md` không tồn tại hoặc nội dung rỗng (`not report_bytes or not report_bytes.strip()`): ném `RuntimeError("Report is empty or missing")`.
   - Nếu `sources.json` không tồn tại hoặc không phải cú pháp JSON hợp lệ: ném `RuntimeError("Invalid sources.json")`.
3. Ghi 3 tệp vào thư mục `reports/`:
   - `reports/<slug>.md`: Nội dung báo cáo Markdown.
   - `reports/<slug>.sources.json`: Danh sách nguồn.
   - `reports/<slug>.meta.json`: Bằng chứng chấm điểm chứa:
     ```json
     {
       "topic": topic,
       "model": model_name,
       "elapsed_s": elapsed_s,
       "subagent_calls": subagent_calls,
       "tool_calls": tool_calls,
       "tokens": tokens,
       "n_sources": len(sources_data),
       "source_families": sorted(list({s["source"] for s in sources_data if "source" in s}))
     }
     ```

### 3.5 Cài đặt `main(topic)` (TODO 5)
```python
def main(topic):
    topic = topic.strip()
    if not topic:
        print("Usage: python research.py '<topic>'", file=sys.stderr)
        return 2

    model = make_model()
    # Lấy tên định danh mô hình
    model_name = getattr(model, "model_name", getattr(model, "model", str(model)))
    start = time.monotonic()

    with open_sandbox() as backend:
        # 1. Tạo các thư mục cần thiết trong sandbox
        backend.execute("mkdir -p /tmp/work/research/notes /tmp/work/report")

        # 2. Upload các script kiểm tra vào sandbox
        upload(backend, {
            VALIDATOR_PATH: VALIDATOR_SOURCE.read_bytes(),
            FINALIZER_PATH: FINALIZER_SOURCE.read_bytes()
        })

        # 3. Khởi tạo lead agent
        agent = build_lead_agent(backend, model)

        # 4. Chạy quy trình nghiên cứu
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": build_prompt(topic)}]},
                config={"recursion_limit": 1000}
            )
            elapsed = time.monotonic() - start
            report_file = save_outputs(backend, topic, result["messages"], elapsed, model_name)
            print(f"SUCCESS: Report saved to {report_file}")
            return 0
        except Exception as exc:
            print(f"FAILED: {exc}", file=sys.stderr)
            return 1
```

---

## 4. Kiến thức cần học được (Key Learnings & Takeaways)

1. **Quản lý Vòng đời Tài nguyên Ngoại vi (Resource Lifecycle Management)**:
   - Sử dụng Context Manager (`with open_sandbox()`) để đảm bảo không rò rỉ tài nguyên cloud/container kể cả khi có ngoại lệ phát sinh ngoài ý muốn.
2. **Kỹ thuật Trích xuất Metadata trong Hệ thống Agent**:
   - Khai thác đồ thị trạng thái tin nhắn (Messages State) của LangGraph / Deep Agents để bóc tách thông tin hoạt động (telemetry, tool calls, token usage).
3. **Phòng thủ trước trạng thái Fail-Silent**:
   - Nếu Agent thất bại giữa chừng, hệ thống phải phát hiện và dừng lại dứt khoát với exit code 1 thay vì âm thầm tạo file trống, giúp quá trình tự động hóa (CI/CD, Self-Check) bắt đúng lỗi.
