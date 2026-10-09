# HƯỚNG DẪN THỰC HIỆN CHECKPOINT 0: KHỞI TẠO MÔI TRƯỜNG & CẤU HÌNH HỆ THỐNG (Setup)

---

## 1. Mục tiêu (Objectives)
- Thiết lập môi trường ảo Python 3.11+ cô lập, chuẩn hóa các gói phụ thuộc theo `requirements.txt`.
- Cấu hình các biến môi trường nhạy cảm (`.env`) gồm LLM Provider, Sandbox Backend (Daytona hoặc Docker), và Exa API.
- Đảm bảo cơ chế bảo mật (Secret Hygiene): kiểm tra `.gitignore` để không bao giờ làm rò rỉ khóa API lên Git.

---

## 2. Yêu cầu chi tiết (Requirements & Rubric Alignment)

### 2.1 Điểm Rubric liên quan
- **Tiêu chí 6.1 (3 điểm)**: `.env` được bỏ qua bởi Git, không có khóa bí mật nào lọt vào Git history.
- **Tiêu chí 6.4 (2 điểm)**: Cài đặt đầy đủ và chuẩn xác các dependencies từ `requirements.txt`.
- **Tiêu chí 3.2 (4 điểm)**: Đảm bảo Sandbox có sẵn (Daytona API Key hợp lệ hoặc Docker daemon đang chạy trên máy).

### 2.2 Các tài nguyên cần chuẩn bị
1. **Mô hình LLM hỗ trợ Tool Calling**:
   - OpenAI (`gpt-4o`, `gpt-4o-mini`)
   - Google Gemini (`gemini-1.5-flash`, `gemini-1.5-pro` qua `google_genai`)
   - Anthropic (`claude-3-5-sonnet-20241022`)
   - Hoặc OpenAI-Compatible (OpenRouter, Groq, Ollama...)
2. **Sandbox Engine**:
   - Lựa chọn 1 (Khuyến nghị): Tài khoản Daytona Cloud (`DAYTONA_API_KEY` từ [https://app.daytona.io](https://app.daytona.io)).
   - Lựa chọn 2: Docker Desktop chạy cục bộ trên máy (`SANDBOX=docker`).
3. **Exa API Key**:
   - Tạo khóa miễn phí tại [https://dashboard.exa.ai/api-keys](https://dashboard.exa.ai/api-keys).

---

## 3. Toàn bộ lệnh thực hiện (Step-by-Step Commands)

### Bước 1: Tạo và kích hoạt môi trường ảo (Virtual Environment)
Trên Windows (PowerShell):
```powershell
# 1. Tạo virtual environment (Python 3.11 trở lên)
python -m venv .venv

# 2. Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1
```

*Nếu gặp lỗi `Execution_Policies` trên PowerShell, chạy lệnh này trước:*
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

*(Đối với CMD)*:
```cmd
.\.venv\Scripts\activate.bat
```

*(Đối với Linux / macOS)*:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Bước 2: Nâng cấp pip và cài đặt thư viện
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Bước 3: Tạo và thiết lập tệp cấu hình `.env`
Sao chép mẫu cấu hình:
```powershell
# Windows PowerShell:
Copy-Item .env.example .env

# Hoặc CMD / Linux:
# cp .env.example .env
```

Mở tệp `.env` và điền thông tin của bạn:
```env
# 1. Cấu hình LLM (Chọn 1 trong các cách sau)
# Cách A: Dùng Google Gemini (Khuyến nghị rẻ & nhanh)
LAB_MODEL=google_genai:gemini-1.5-flash
GOOGLE_API_KEY=AIzaSy...

# Hoặc Cách B: Dùng OpenAI
# LAB_MODEL=openai:gpt-4o-mini
# OPENAI_API_KEY=sk-proj-...

# Hoặc Cách C: Dùng OpenRouter
# LAB_BASE_URL=https://openrouter.ai/api/v1
# LAB_MODEL=openai/gpt-4o-mini
# LAB_API_KEY=sk-or-...

# 2. Cấu hình Sandbox
# Lựa chọn 1: Dùng Daytona Cloud (mặc định)
DAYTONA_API_KEY=dtn_...

# Lựa chọn 2: Dùng Docker cục bộ (nếu không có Daytona)
# SANDBOX=docker
# SANDBOX_IMAGE=python:3.12-slim

# 3. Cấu hình Exa MCP (Tìm kiếm Web)
EXA_API_KEY=exa_...
```

---

### Bước 4: Kiểm tra nhanh môi trường (Sanity Check)
Chạy lệnh kiểm tra import các thư viện cốt lõi:
```powershell
python -c "import deepagents, langchain_daytona, httpx, dotenv; print('Environment OK!')"
```

---

## 4. Kiến thức cần học được (Key Learnings & Takeaways)

1. **Nguyên lý Môi trường cô lập (Environment Isolation)**:
   - Hiểu lý do phải dùng `venv`: Đảm bảo các phiên bản của `deepagents`, `langchain`, `httpx` không bị xung đột với các project Python khác trên máy host.
2. **Kỹ thuật nạp cấu hình 12-Factor App**:
   - Tách biệt mã nguồn và cấu hình môi trường qua `.env`. Sử dụng thư viện `python-dotenv` để tự động hóa nạp cấu hình.
3. **Bảo mật Bí mật nhà phát triển (Secret Management)**:
   - Hiểu tại sao `.env` phải luôn được khai báo trong `.gitignore`. Nhận thức được rủi ro bị quét API keys công khai trên GitHub dẫn đến mất tiền và bị lộ thông tin.
