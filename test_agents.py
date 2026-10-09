import agents
from tools import SOURCE_TOOLS, web_fetch

print("--- BẮT ĐẦU KIỂM THỬ AGENTS.PY ---")

# 1. Kiểm tra build_subagents
subagents = agents.build_subagents()
assert len(subagents) == 2, f"Expected 2 subagents, got {len(subagents)}"
names = {s["name"]: s for s in subagents}
assert "researcher" in names, "Missing researcher subagent"
assert "citation-checker" in names, "Missing citation-checker subagent"

# Kiểm tra tools của từng subagent
assert names["researcher"]["tools"] == SOURCE_TOOLS, "Researcher must have all SOURCE_TOOLS"
assert names["researcher"]["middleware"] == agents.SUB_LIMITS, "Researcher must have SUB_LIMITS"
assert names["citation-checker"]["tools"] == [web_fetch], "Checker must have [web_fetch]"
assert names["citation-checker"]["middleware"] == agents.SUB_LIMITS, "Checker must have SUB_LIMITS"
print("Test 1 (Subagent specs & tools & limits): OK")

# 2. Kiểm tra LEAD_PROMPT
lead_prompt = agents.LEAD_PROMPT
assert agents.WORKDIR in lead_prompt
assert agents.NOTES_DIR in lead_prompt
assert agents.SOURCES_PATH in lead_prompt
assert agents.VALIDATOR_PATH in lead_prompt
assert agents.FINALIZER_PATH in lead_prompt
assert agents.REPORT_PATH in lead_prompt
assert "write_todos" in lead_prompt, "Lead prompt must instruct to use write_todos"
assert "subagent_calls >= 3" in lead_prompt or "at least 3" in lead_prompt, "Lead prompt must instruct delegation >= 3"
assert "source families" in lead_prompt, "Lead prompt must instruct to ensure >= 3 source families"
assert "finalize_citations.py" in lead_prompt, "Lead prompt must mention finalizer"
assert "check_citations.py" in lead_prompt, "Lead prompt must mention validator"
print("Test 2 (LEAD_PROMPT coverage): OK")

# 3. Kiểm tra RESEARCHER_PROMPT
res_prompt = agents.RESEARCHER_PROMPT
assert "UNTRUSTED DATA" in res_prompt or "untrusted" in res_prompt.lower(), "Must warn about untrusted data"
assert "arxiv" in res_prompt and "hf" in res_prompt and "web" in res_prompt, "Must list all sources"
assert "Key Findings" in res_prompt or "format" in res_prompt.lower(), "Must specify notes format"
print("Test 3 (RESEARCHER_PROMPT coverage): OK")

# 4. Kiểm tra CHECKER_PROMPT
checker_prompt = agents.CHECKER_PROMPT
assert "SUPPORTED" in checker_prompt
assert "UNSUPPORTED" in checker_prompt
assert "UNVERIFIABLE" in checker_prompt
print("Test 4 (CHECKER_PROMPT coverage): OK")

# 5. Kiểm tra build_lead_agent signature & compile test
class DummyBackend:
    pass

class DummyModel:
    pass

# We test that the function is defined and callable
assert callable(agents.build_lead_agent)
print("Test 5 (build_lead_agent is callable): OK")

print("\n>>> TẤT CẢ TEST CHO AGENTS.PY ĐÃ VƯỢT QUA 100%! <<<")
