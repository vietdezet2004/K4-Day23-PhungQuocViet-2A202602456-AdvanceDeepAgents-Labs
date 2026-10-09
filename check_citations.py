"""check_citations.py - STUDENT IMPLEMENTS `check`.   Runs INSIDE the sandbox (standard library only).

research.py uploads this file to the sandbox and the lead agent runs it with the `execute` tool:
    python3 /tmp/work/research/check_citations.py [report.md] [sources.json]
It must exit 0 and print "OK: ..." when the report is consistent, else print each problem and exit 1.
"""
import json
import sys

REPORT = "/tmp/work/report/report.md"
SOURCES = "/tmp/work/research/sources.json"


import re

_GROUP = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\](?!\()")   # [3]  [1, 2]  [1-3]  [2-3]; not [3](link)
_CODE = re.compile(r"(```.*?```|`[^`\n]*`)", re.DOTALL)
_REF_HEADING = re.compile(r"(?m)^##[ \t]+References[ \t]*$")
_REF_LINE = re.compile(r"^\s*\[(\d+)\](.*)$")
_URL = re.compile(r"https?://[^\s)\]]+")


def _group_numbers(group):
    numbers = []
    for part in re.split(r"\s*,\s*", group):
        span = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", part)
        if span:
            a, b = int(span.group(1)), int(span.group(2))
            numbers.extend(range(a, b + 1) if 0 <= b - a <= 200 else [a, b])
        else:
            numbers.append(int(part))
    return numbers


def check(report_text, sources):
    """Return a list of problem strings (empty list = OK)."""
    problems = []

    # 1. Sources list validation
    if not isinstance(sources, list) or len(sources) == 0:
        return ["no sources in sources.json"]

    seen_urls = {}
    source_by_n = {}
    for entry in sources:
        if not isinstance(entry, dict):
            problems.append(f"source entry is not an object: {entry!r}")
            continue

        n = entry.get("n")
        if not isinstance(n, int) or isinstance(n, bool):
            problems.append(f"source 'n' must be an int, got {n!r} in {entry!r}")
        elif n in source_by_n:
            problems.append(f"duplicate source number [{n}] in sources.json")
        else:
            source_by_n[n] = entry

        url = entry.get("url")
        if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
            problems.append(f"source [{n}]: url {url!r} must start with http:// or https://")
        else:
            clean_entry_url = url.strip()
            if clean_entry_url in seen_urls:
                problems.append(f"duplicate url in sources.json: '{clean_entry_url}' (used in [{seen_urls[clean_entry_url]}] and [{n}])")
            else:
                seen_urls[clean_entry_url] = n

    # 2. Split report at '## References' heading
    matches = list(_REF_HEADING.finditer(report_text))
    if not matches:
        problems.append("missing '## References' heading in report")
        body = report_text
        ref_section = ""
    else:
        body = report_text[:matches[-1].start()]
        ref_section = report_text[matches[-1].end():]

    # 3. Extract citations [n] from BODY only (ignoring code spans/blocks and markdown links)
    segments = _CODE.split(body)
    cited_in_body = set()
    for i, segment in enumerate(segments):
        if i % 2:  # Odd segments are code blocks
            continue
        for match in _GROUP.finditer(segment):
            for num in _group_numbers(match.group(1)):
                cited_in_body.add(num)

    # 4. Cross-check body citations and sources.json
    for num in sorted(cited_in_body):
        if num not in source_by_n:
            problems.append(f"[{num}] cited but missing from sources.json")

    for n in sorted(source_by_n.keys()):
        if n not in cited_in_body:
            problems.append(f"source [{n}] never cited")

    # 5. Check '## References' section
    if matches:
        ref_lines_by_n = {}
        for line in ref_section.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            m = _REF_LINE.match(line_str)
            if m:
                n_val = int(m.group(1))
                if n_val in ref_lines_by_n:
                    problems.append(f"reference [{n_val}] appears more than once in '## References'")
                else:
                    ref_lines_by_n[n_val] = line_str

        # Every source needs exactly one reference line
        for n in sorted(source_by_n.keys()):
            if n not in ref_lines_by_n:
                problems.append(f"source [{n}] has no reference line in '## References'")

        # No reference number that is not in sources
        for n in sorted(ref_lines_by_n.keys()):
            if n not in source_by_n:
                problems.append(f"reference [{n}] in '## References' is not in sources.json")
            else:
                # Each reference line holds exactly ONE http(s) URL matching that source's url
                line_str = ref_lines_by_n[n]
                urls = _URL.findall(line_str)
                if len(urls) == 0:
                    problems.append(f"reference line [{n}] contains no URL: '{line_str}'")
                elif len(urls) > 1:
                    problems.append(f"reference line [{n}] contains multiple URLs (bundled sources): '{line_str}'")
                else:
                    clean_url = urls[0].rstrip(".,;)>\"'")
                    expected_url = source_by_n[n]["url"].strip()
                    if clean_url != expected_url:
                        problems.append(
                            f"reference line [{n}] URL '{clean_url}' does not match source URL '{expected_url}'"
                        )

    return problems


def main(argv):
    report_path = argv[1] if len(argv) > 1 else REPORT
    sources_path = argv[2] if len(argv) > 2 else SOURCES
    try:
        with open(report_path, encoding="utf-8") as f:
            report = f.read()
        with open(sources_path, encoding="utf-8") as f:
            sources = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read inputs: {exc}")
        return 1
    problems = check(report, sources)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(sources)} sources, all citations resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
