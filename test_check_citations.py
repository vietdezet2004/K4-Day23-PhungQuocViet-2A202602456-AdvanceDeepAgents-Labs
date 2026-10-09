from check_citations import check

# 1. Báo cáo chuẩn hoàn hảo (Valid report)
sources_1 = [
    {"n": 1, "url": "https://arxiv.org/abs/2501.00001", "title": "Paper 1"},
    {"n": 2, "url": "https://huggingface.co/papers/2501.00002", "title": "Paper 2"},
    {"n": 3, "url": "https://example.com/blog", "title": "Web 3"}
]
report_1 = """# Survey
First finding [1]. Second finding [2]. Third finding [3].

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025-01-01)
[2] Paper 2. hf-search. https://huggingface.co/papers/2501.00002 (2025-01-02)
[3] Web 3. web. https://example.com/blog (2025-01-03)
"""
assert check(report_1, sources_1) == []
print("Case 1 (Perfect Report): OK")

# 2. Khối mã và Markdown link không được tính là trích dẫn
report_2 = """# Survey
First finding [1].
```python
# [99] in code block
x = [2]
```
Inline `[98]` and markdown link [100](https://arxiv.org/abs/2501.00001).

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025)
"""
assert check(report_2, [sources_1[0]]) == []
print("Case 2 (Ignore Code & Markdown links): OK")

# 3. Trích dẫn dạng gộp [1, 2] và dải [1-3], [1–3]
report_3 = """# Survey
Group 1: [1, 2].
Group 2: [1-3].
En-dash: [1–3].

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025)
[2] Paper 2. hf-search. https://huggingface.co/papers/2501.00002 (2025)
[3] Web 3. web. https://example.com/blog (2025)
"""
assert check(report_3, sources_1) == []
print("Case 3 (Grouped [1, 2] and Range [1-3]): OK")

# 4. Trích dẫn số không có trong sources.json
report_4 = """# Survey
Finding with invalid citation [99].

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025)
"""
errs_4 = check(report_4, [sources_1[0]])
assert any("[99] cited but missing" in e for e in errs_4)
assert any("source [1] never cited" in e for e in errs_4)
print("Case 4 (Missing & Uncited Detection): OK")

# 5. Gộp nhiều nguồn vào 1 số tham khảo (Bundled multiple URLs)
report_5 = """# Survey
Finding [1].

## References
[1] Paper 1: https://arxiv.org/abs/2501.00001 and Paper B: https://example.com/other (2025)
"""
errs_5 = check(report_5, [sources_1[0]])
assert any("bundled sources" in e for e in errs_5)
print("Case 5 (Bundled URLs detected): OK")

# 6. Sai khác URL giữa dòng tham khảo và sources.json
report_6 = """# Survey
Finding [1].

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/different_url (2025)
"""
errs_6 = check(report_6, [sources_1[0]])
assert any("does not match source URL" in e for e in errs_6)
print("Case 6 (URL Mismatch detected): OK")

# 7. Thiếu heading '## References'
report_7 = """# Survey
Finding [1].
"""
errs_7 = check(report_7, [sources_1[0]])
assert any("missing '## References'" in e for e in errs_7)
print("Case 7 (Missing References heading): OK")

# 8. Trùng lặp URL trong sources.json
sources_dup_url = [
    {"n": 1, "url": "https://arxiv.org/abs/2501.00001"},
    {"n": 2, "url": "https://arxiv.org/abs/2501.00001"}
]
errs_8 = check(report_1, sources_dup_url)
assert any("duplicate url in sources.json" in e for e in errs_8)
print("Case 8 (Duplicate URL in sources.json): OK")

# 9. Trùng lặp số 'n' trong sources.json
sources_dup_n = [
    {"n": 1, "url": "https://arxiv.org/abs/2501.00001"},
    {"n": 1, "url": "https://arxiv.org/abs/2501.00002"}
]
errs_9 = check(report_1, sources_dup_n)
assert any("duplicate source number [1]" in e for e in errs_9)
print("Case 9 (Duplicate 'n' in sources.json): OK")

# 10. Kiểu dữ liệu 'n' không phải int (hoặc là bool)
sources_bad_n = [
    {"n": True, "url": "https://arxiv.org/abs/2501.00001"},
    {"n": "2", "url": "https://arxiv.org/abs/2501.00002"}
]
errs_10 = check(report_1, sources_bad_n)
assert any("source 'n' must be an int" in e for e in errs_10)
print("Case 10 (Bad 'n' types): OK")

# 11. sources.json rỗng
errs_11 = check(report_1, [])
assert errs_11 == ["no sources in sources.json"]
print("Case 11 (Empty sources): OK")

# 12. Dòng tham khảo không có URL
report_12 = """# Survey
Finding [1].

## References
[1] Paper 1 without any URL link.
"""
errs_12 = check(report_12, [sources_1[0]])
assert any("contains no URL" in e for e in errs_12)
print("Case 12 (Reference line missing URL): OK")

print("\n>>> TẤT CẢ 12 TEST CASES BẢO MẬT & ĐÚNG ĐẮN ĐÃ VƯỢT QUA 100%! <<<")
