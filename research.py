"""research.py - STUDENT IMPLEMENTS.  The main script.   Guide: GUIDE.md, part 3.

Usage:  python research.py "survey about world model"
Result: reports/<slug>.md   reports/<slug>.sources.json   reports/<slug>.meta.json
"""
import json
import os  # noqa: F401
import re
import sys
import time
from collections import Counter
from pathlib import Path

from agents import FINALIZER_PATH, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH, WORKDIR, build_lead_agent
from model import make_model
from sandbox import download, open_sandbox, upload

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"
VALIDATOR_SOURCE = ROOT / "check_citations.py"
FINALIZER_SOURCE = ROOT / "finalize_citations.py"   # provided: uploaded next to your validator


def slugify(topic):
    """Turn a topic into a safe file name: lower case, runs of non-word characters become one "-", max 60 chars,
    never empty (fall back to "topic"). The topic is user input: "../../x" must not escape reports/."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(topic or "").lower()).strip("-")
    s = s[:60].strip("-")
    return s if s else "topic"


def build_prompt(topic):
    """The user message sent to the lead agent."""
    clean_topic = str(topic or "").strip()
    return (
        f"Conduct a comprehensive, deep research survey on the topic: '{clean_topic}'.\n\n"
        "Please follow your workflow strictly:\n"
        "1. Plan with write_todos and split this topic into at least 3 distinct sub-questions.\n"
        "2. Delegate sub-questions to researcher subagents using the task tool in parallel (at least 3 subagent calls). "
        "MANDATORY: Make sure to assign different sources across subagents (researcher 1 uses arxiv_search, researcher 2 uses hf_daily_papers/hf_search_papers, researcher 3 uses web_search/web_fetch) "
        "so that at least 3 distinct source families (out of arxiv, hf-daily, hf-search, web) are collected!\n"
        "3. Review notes and merge sources into sources.json. Verify that sources.json contains at least 3 distinct source families.\n"
        "4. Write the survey report body into report.md following REPORT_TEMPLATE.md (do NOT write ## References). "
        "CRITICAL: You MUST explicitly cite sources [n] from all 3 source families in your text (finalize_citations.py removes any source not cited in the text).\n"
        "5. Run finalize_citations.py via execute to generate ## References and renumber citations.\n"
        "6. Run check_citations.py via execute and fix any issues until it reports OK.\n"
        "7. Perform a spot check on key claims using the citation-checker subagent."
    )


def summarize(messages, elapsed, model_name):
    """Return {"model", "elapsed_s", "subagent_calls", "tool_calls": {name: count}, "tokens": {"input", "output"}}."""
    tool_counts = Counter()
    total_input = 0
    total_output = 0

    for msg in messages:
        # Tool calls count
        calls = []
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            calls = msg.tool_calls
        elif isinstance(msg, dict) and msg.get("tool_calls"):
            calls = msg["tool_calls"]

        for call in calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                tool_counts[str(name)] += 1

        # Token usage count
        usage = getattr(msg, "usage_metadata", None)
        if isinstance(msg, dict):
            usage = usage or msg.get("usage_metadata")
        if usage and isinstance(usage, dict):
            total_input += usage.get("input_tokens", 0) or 0
            total_output += usage.get("output_tokens", 0) or 0

    return {
        "model": str(model_name),
        "elapsed_s": round(float(elapsed), 1),
        "subagent_calls": tool_counts.get("task", 0),
        "tool_calls": dict(tool_counts),
        "tokens": {
            "input": total_input,
            "output": total_output,
        },
    }


def save_outputs(backend, topic, messages, elapsed, model_name, reports_dir=REPORTS):
    """Download the report from the sandbox and write the three files into reports_dir. Return the report path."""
    files = download(backend, [REPORT_PATH, SOURCES_PATH])
    report_bytes = files.get(REPORT_PATH)
    sources_bytes = files.get(SOURCES_PATH)

    if not report_bytes or not report_bytes.strip():
        raise RuntimeError(f"Report is missing or empty at {REPORT_PATH}")

    if not sources_bytes or not sources_bytes.strip():
        raise RuntimeError(f"sources.json is missing or empty at {SOURCES_PATH}")

    try:
        sources_data = json.loads(sources_bytes.decode("utf-8"))
        if not isinstance(sources_data, list):
            raise ValueError("sources.json must be a JSON array")
    except Exception as exc:
        raise RuntimeError(f"Invalid sources.json: {exc}") from exc

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(topic)
    summary_data = summarize(messages, elapsed, model_name)

    distinct_families = sorted(list({
        s["source"] for s in sources_data if isinstance(s, dict) and "source" in s
    }))

    meta_data = {
        "topic": topic,
        **summary_data,
        "n_sources": len(sources_data),
        "source_families": distinct_families,
    }

    # Write the three files
    sources_path = reports_dir / f"{slug}.sources.json"
    sources_path.write_bytes(sources_bytes)

    meta_path = reports_dir / f"{slug}.meta.json"
    meta_path.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = reports_dir / f"{slug}.md"
    report_path.write_bytes(report_bytes)

    return report_path


def main(topic):
    """Return the process exit code (0 ok, 1 failed run, 2 no topic)."""
    clean_topic = topic.strip()
    if not clean_topic:
        print("Usage: python research.py \"<topic>\"", file=sys.stderr)
        return 2

    model = make_model()
    model_name = getattr(model, "model_name", getattr(model, "model", str(model)))
    start = time.monotonic()

    with open_sandbox() as backend:
        backend.execute(f"mkdir -p {WORKDIR}/research/notes {WORKDIR}/report")
        upload(backend, {
            VALIDATOR_PATH: VALIDATOR_SOURCE.read_bytes(),
            FINALIZER_PATH: FINALIZER_SOURCE.read_bytes(),
        })
        agent = build_lead_agent(backend, model)
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": build_prompt(clean_topic)}]},
                config={"recursion_limit": 1000},
            )
            elapsed = time.monotonic() - start
            messages = result.get("messages", []) if isinstance(result, dict) else []
            report_file = save_outputs(backend, clean_topic, messages, elapsed, model_name)
            print(f"Report saved: {report_file}")
            return 0
        except RuntimeError as exc:
            print(f"FAILED: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main(" ".join(sys.argv[1:])))
