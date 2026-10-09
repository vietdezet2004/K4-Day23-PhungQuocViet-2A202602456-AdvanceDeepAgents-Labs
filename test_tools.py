import os
import time
import httpx
from tools import RetryableError, with_retry, _redact_key, arxiv_search, hf_daily_papers, hf_search_papers, web_search, web_fetch

print("--- BẮT ĐẦU KIỂM THỬ TOOLS.PY ---")

# 1. Test with_retry: Thành công ngay lần đầu
calls = 0
def fn_success():
    global calls
    calls += 1
    return "ok"
assert with_retry(fn_success) == "ok"
assert calls == 1
print("Test 1 (Success first try): OK")

# 2. Test with_retry: Retry thành công sau 2 lần lỗi
retry_count = 0
def fn_retry_success():
    global retry_count
    retry_count += 1
    if retry_count < 3:
        raise RetryableError("temporary glitch")
    return "recovered"
start = time.time()
res = with_retry(fn_retry_success, attempts=5, base=0.05, cap=1.0)
assert res == "recovered"
assert retry_count == 3
print("Test 2 (Recover after retries): OK")

# 3. Test with_retry: Bỏ cuộc sau N lần thử và không ngủ thêm sau lần cuối
fail_calls = 0
def fn_always_fail():
    global fail_calls
    fail_calls += 1
    raise RetryableError("persistent fail")

try:
    with_retry(fn_always_fail, attempts=3, base=0.05, cap=1.0)
    assert False, "Should have raised RetryableError"
except RetryableError:
    assert fail_calls == 3
print("Test 3 (Give up after N attempts): OK")

# 4. Test with_retry: Lỗi không thuộc diện retryable phải nổi lên ngay lập tức
non_retry_calls = 0
def fn_type_error():
    global non_retry_calls
    non_retry_calls += 1
    raise TypeError("programming bug")

try:
    with_retry(fn_type_error, attempts=5)
    assert False, "Should have raised TypeError"
except TypeError:
    assert non_retry_calls == 1
print("Test 4 (Non-retryable raises immediately): OK")

# 5. Test with_retry: Tôn trọng Retry-After
ra_calls = 0
def fn_retry_after():
    global ra_calls
    ra_calls += 1
    if ra_calls < 2:
        raise RetryableError("rate limited", retry_after=0.1)
    return "ok_ra"

start = time.time()
res_ra = with_retry(fn_retry_after, attempts=3, base=10.0, cap=30.0)
elapsed = time.time() - start
assert res_ra == "ok_ra"
assert 0.08 <= elapsed < 1.0  # Should use retry_after (0.1s), not base (10.0s)
print("Test 5 (Respects Retry-After): OK")

# 6. Test che giấu EXA_API_KEY
os.environ["EXA_API_KEY"] = "test-dummy-key"
leak_str = "Error calling https://mcp.exa.ai/mcp?exaApiKey=test-dummy-key failed"
redacted = _redact_key(leak_str)
assert "test-dummy-key" not in redacted
assert "[REDACTED]" in redacted
print("Test 6 (Redact EXA_API_KEY): OK")

# 7. Test arXiv sanitization: Truy vấn rỗng hoặc toàn ký tự lạ -> NO RESULTS không gọi mạng
empty_res = arxiv_search.invoke({"query": "??? ::: '''' \"\"\""})
assert empty_res == "NO RESULTS"
print("Test 7 (arXiv empty/bad query -> NO RESULTS): OK")

print("\n>>> TẤT CẢ UNIT TESTS CHO TOOLS.PY ĐÃ VƯỢT QUA 100%! <<<")
