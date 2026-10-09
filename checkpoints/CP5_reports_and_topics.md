# HƯỚNG DẪN THỰC HIỆN CHECKPOINT 5: CHẠY NGHIÊN CỨU 5 CHỦ ĐỀ & CHẤT LƯỢNG BÁO CÁO (reports/)

---

## 1. Mục tiêu (Objectives)
- Tiến hành thực thi hệ thống Deep Research để tạo ra đầy đủ **5 bộ báo cáo** cho 5 chủ đề quy định trong `topics.md`.
- Đảm bảo mỗi báo cáo đạt chất lượng học thuật cao: đúng cấu trúc chuẩn của `REPORT_TEMPLATE.md`, tổng hợp so sánh đa chiều theo chủ đề (không liệt kê đơn thuần), trích dẫn chính xác, có cả công trình kinh điển lẫn bài báo 2 năm gần nhất.
- Đảm bảo đầy đủ bộ ba tệp cho mỗi đề tài trong thư mục `reports/`:
  - `<slug>.md`
  - `<slug>.sources.json`
  - `<slug>.meta.json`

---

## 2. Yêu cầu chi tiết (Requirements & Rubric Alignment)

### 2.1 Điểm Rubric liên quan (Tổng cộng 40 điểm: Phần 4 + Phần 5)
- **Tiêu chí 4.2 Thẩm định mẫu trích dẫn (8 điểm)**:
  - Giảng viên sẽ lấy mẫu ngẫu nhiên 5 trích dẫn trong mỗi báo cáo. Nguồn phải có thật trên thực tế và khẳng định được trích dẫn phải đúng với nội dung bài báo. Nếu phát hiện URL/nguồn bịa đặt, báo cáo đó nhận 0 điểm mục 4.
- **Tiêu chí 5 Chất lượng báo cáo (25 điểm - 5 điểm/báo cáo)**:
  1. **Đúng cấu trúc chuẩn (1.0đ)**: Bắt buộc đủ các phần: `# Title`, `## TL;DR`, `## Background`, `## <Theme 1..k>`, `## Trends and open problems`, `## References`.
  2. **Tổng hợp theo chủ đề (1.5đ)**: So sánh, đối chiếu các trường phái/phương pháp; cấm viết theo kiểu "mỗi bài báo một đoạn văn".
  3. **Chính xác và cụ thể (1.5đ)**: Có tên mô hình, thuật toán, tác giả, năm công bố và số liệu định lượng (benchmark).
  4. **Độ phủ thời gian và nguồn (0.5đ)**: Kết hợp công trình nền tảng và bài báo trong 2 năm gần nhất (2024 - 2026), tận dụng các họ nguồn khác nhau.
  5. **Xu hướng và vấn đề mở (0.5đ)**: Nêu rõ thách thức chưa giải quyết, hướng đi tương lai.
- **Tiêu chí 2.1 & 2.2 Đảm bảo siêu dữ liệu**:
  - `subagent_calls >= 3` cho mọi đề tài.
  - `source_families` chứa ít nhất 3 trong 4 họ nguồn (`arxiv`, `hf-daily`, `hf-search`, `web`).

---

## 3. Danh sách 5 chủ đề bắt buộc (topics.md)

| STT | Chủ đề (`topic`) | Slug dự kiến |
|---|---|---|
| 1 | `survey about world model` | `survey-about-world-model` |
| 2 | `survey about reinforcement learning for LLM reasoning` | `survey-about-reinforcement-learning-for-llm-reasoning` |
| 3 | `survey about LLM agents and tool use` | `survey-about-llm-agents-and-tool-use` |
| 4 | `survey about video and multimodal generation` | `survey-about-video-and-multimodal-generation` |
| 5 | `survey about efficient inference and small language models` | `survey-about-efficient-inference-and-small-language-models` |

---

## 4. Hướng dẫn thực hiện chi tiết (Execution Workflow)

### Bước 1: Chuẩn bị biến môi trường `.env`
Đảm bảo đã cấu hình đầy đủ API Key trong `.env`:
```env
# Chọn mô hình hỗ trợ Tool Calling tốt (OpenAI GPT-4o-mini / GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro/Flash, v.v.)
LAB_MODEL=google_genai:gemini-1.5-flash
GOOGLE_API_KEY=your_key_here

# Hoặc dùng OpenAI-compatible:
# LAB_BASE_URL=https://openrouter.ai/api/v1
# LAB_MODEL=openai/gpt-4o-mini
# LAB_API_KEY=your_openrouter_key

# Sandbox
SANDBOX=daytona
DAYTONA_API_KEY=your_daytona_key
# Hoặc nếu không có Daytona:
# SANDBOX=docker

# Exa MCP (Khuyến nghị để không bị giới hạn IP)
EXA_API_KEY=your_exa_key
```

### Bước 2: Chạy lần lượt từng chủ đề
Chạy từng lệnh và theo dõi log thực thi:
```bash
python research.py "survey about world model"
python research.py "survey about reinforcement learning for LLM reasoning"
python research.py "survey about LLM agents and tool use"
python research.py "survey about video and multimodal generation"
python research.py "survey about efficient inference and small language models"
```

### Bước 3: Kiểm tra tính hợp lệ của từng báo cáo
Sau khi chạy xong mỗi đề tài, chạy ngay kiểm tra trích dẫn:
```bash
python check_citations.py reports/<slug>.md reports/<slug>.sources.json
```
Lệnh phải in ra dòng: `OK: N sources, all citations resolve`.

### Bước 4: Kiểm tra siêu dữ liệu `<slug>.meta.json`
Mở file `.meta.json` và kiểm tra 2 điều kiện tiên quyết:
1. `"subagent_calls"`: Giá trị phải $\ge 3$.
2. `"source_families"`: Số lượng phần tử khác nhau phải $\ge 3$ (ví dụ: `["arxiv", "hf-search", "web"]`).

*Nếu không đạt*: Đừng sửa tay file kết quả! Hãy quay lại tinh chỉnh Prompt trong `agents.py` để Lead Agent bắt buộc phải giao việc nhiều hơn và bắt buộc phải bổ sung nguồn nếu thiếu họ nguồn, sau đó chạy lại đề tài đó.

---

## 5. Kiến thức cần học được (Key Learnings & Takeaways)

1. **Khả năng tổng hợp học thuật của LLM (Literature Synthesis vs. Listing)**:
   - Học cách viết Prompt định hướng LLM tổng hợp so sánh các kỹ thuật (Paradigm Comparison) thay vì tóm tắt tuần tự từng bài báo một cách rời rạc.
2. **Kỹ thuật Triệt tiêu Ảo giác (Hallucination Mitigation)**:
   - Hiểu rõ tầm quan trọng của việc neo giữ thông tin (Grounding) dựa trên dữ liệu trích xuất từ các bài báo thực tế trên arXiv và Hugging Face.
3. **Tính ngẫu nhiên của LLM và Prompt Hardening**:
   - Nhận thức được rằng một Agent có thể chạy thành công ở lần 1 nhưng thất bại ở lần 2. Do đó, việc xây dựng các chốt chặn tự động (`finalize_citations.py`, `check_citations.py`, middleware giới hạn) là chìa khóa để đạt được độ tin cậy cấp độ sản phẩm (production-grade reliability).
