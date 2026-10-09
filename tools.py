"""tools.py - STUDENT IMPLEMENTS.  Source tools for the research agents.   Guide: GUIDE.md, part 1.

Rules for every tool:
  * runs on the HOST (not in the sandbox): API keys must never enter the sandbox;
  * returns a STRING (JSON text of compact records) and NEVER raises:
        "NO RESULTS"  when the source answers with nothing,
        "ERROR: ..."  when the source keeps failing after the retries (the agent then tries another source);
  * the docstring is the tool description the LLM reads: keep it precise (what it does, what it returns, when to use it).
Try your tools without any agent:   python tools.py
"""
import json  # noqa: F401
import os  # noqa: F401
import time  # noqa: F401
import xml.etree.ElementTree  # noqa: F401  (arXiv answers with Atom XML)

import httpx  # noqa: F401
from langchain_core.tools import tool

import random
import re

# ---- constants (given) ----
ARXIV_URL = "https://export.arxiv.org/api/query"  # https only: http answers 301
HF_DAILY_URL = "https://huggingface.co/api/daily_papers"
HF_SEARCH_URL = "https://huggingface.co/api/papers/search"
EXA_URL = "https://mcp.exa.ai/mcp"

_LAST_ARXIV_CALL = 0.0
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RetryableError(Exception):
    """Given. Raise it inside a call to ask with_retry to wait and try again (retry_after in seconds, optional)."""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


# ---- Helper to redact EXA_API_KEY from errors ----
def _redact_key(text: str) -> str:
    key = os.getenv("EXA_API_KEY")
    if key and key in text:
        text = text.replace(key, "[REDACTED]")
    return text


# ---- TODO 1: retry helper ----
def with_retry(fn, *, attempts=5, base=1.0, cap=30.0):
    """Call fn(); when it raises RetryableError, wait and call it again."""
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as e:
            retry_after = None
            if isinstance(e, RetryableError):
                retry_after = e.retry_after
            elif isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code not in RETRYABLE_STATUS:
                    raise
                ra = e.response.headers.get("Retry-After")
                if ra:
                    try:
                        retry_after = float(ra)
                    except ValueError:
                        retry_after = None
            elif isinstance(e, httpx.TransportError):
                pass
            else:
                raise

            if attempt == attempts - 1:
                raise

            if retry_after is not None and retry_after > 0:
                delay = min(cap, float(retry_after))
            else:
                backoff = min(cap, base * (2 ** attempt))
                delay = min(cap, backoff + random.uniform(0.1, 0.5))

            time.sleep(delay)


# ---- TODO 2: arXiv ----
@tool
def arxiv_search(query: str, max_results: int = 10) -> str:
    """Search arXiv papers by keywords, newest first. Returns a JSON list of {id, url, published, title, summary}."""
    global _LAST_ARXIV_CALL
    try:
        terms = re.findall(r"[\w\-]+", query)
        if not terms:
            return "NO RESULTS"

        # Respect arXiv etiquette: at least 3 seconds between two calls
        now = time.time()
        elapsed = now - _LAST_ARXIV_CALL
        if elapsed < 3.0:
            time.sleep(3.0 - elapsed)
        _LAST_ARXIV_CALL = time.time()

        max_results_clamped = max(1, min(max_results, 30))
        search_query = " AND ".join(f"all:{t}" for t in terms)
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results_clamped,
        }

        def _call():
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(ARXIV_URL, params=params)
                resp.raise_for_status()
                return resp.content

        content = with_retry(_call, attempts=5, base=2.0, cap=60.0)
        root = xml.etree.ElementTree.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if not entries:
            return "NO RESULTS"

        records = []
        for entry in entries:
            id_elem = entry.find("atom:id", ns)
            if id_elem is None or not id_elem.text:
                continue
            raw_id = id_elem.text.split("/abs/")[-1].strip()
            paper_id = re.sub(r"v\d+$", "", raw_id)
            url = f"https://arxiv.org/abs/{paper_id}"

            pub_elem = entry.find("atom:published", ns)
            published = pub_elem.text[:10] if (pub_elem is not None and pub_elem.text) else ""

            title_elem = entry.find("atom:title", ns)
            title = " ".join(title_elem.text.split()) if (title_elem is not None and title_elem.text) else "Untitled"

            sum_elem = entry.find("atom:summary", ns)
            summary = " ".join(sum_elem.text.split())[:600] if (sum_elem is not None and sum_elem.text) else ""

            records.append({
                "id": paper_id,
                "url": url,
                "published": published,
                "title": title,
                "summary": summary,
            })

        return json.dumps(records, ensure_ascii=False) if records else "NO RESULTS"
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


# ---- TODO 3: Hugging Face ----
@tool
def hf_daily_papers(limit: int = 30, date: str = "", keyword: str = "") -> str:
    """Hugging Face Daily Papers = what is trending in AI research. Returns a JSON list of
    {id, url, published, title, summary, upvotes, github, stars} sorted by upvotes. `date` is YYYY-MM-DD (empty = latest).
    `keyword` filters title/summary; there is no topic search on this endpoint (use hf_search_papers for a topic)."""
    try:
        limit_clamped = max(1, min(limit, 100))
        params = {"limit": limit_clamped}
        if date:
            params["date"] = date.strip()

        def _call():
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(HF_DAILY_URL, params=params)
                resp.raise_for_status()
                return resp.json()

        items = with_retry(_call, attempts=5, base=1.0, cap=30.0)
        if not isinstance(items, list) or not items:
            return "NO RESULTS"

        records = []
        kw = keyword.strip().lower()
        for item in items:
            if not isinstance(item, dict):
                continue
            paper = item.get("paper") if isinstance(item.get("paper"), dict) else item
            pid = paper.get("id") or item.get("id")
            if not pid:
                continue

            title = " ".join(str(paper.get("title") or item.get("title") or "").split())
            raw_summary = paper.get("summary") or item.get("summary") or ""
            summary = " ".join(str(raw_summary).split())[:600]

            if kw:
                combined = f"{title} {summary}".lower()
                if kw not in combined:
                    continue

            published = str(paper.get("publishedAt") or item.get("publishedAt") or "")[:10]
            upvotes = paper.get("upvotes") or item.get("upvotes") or 0
            github = paper.get("githubRepo") or item.get("githubRepo") or ""
            stars = paper.get("githubStars") or item.get("githubStars") or 0

            records.append({
                "id": str(pid),
                "url": f"https://huggingface.co/papers/{pid}",
                "published": published,
                "title": title,
                "summary": summary,
                "upvotes": int(upvotes) if isinstance(upvotes, (int, float)) else 0,
                "github": str(github) if github else "",
                "stars": int(stars) if isinstance(stars, (int, float)) else 0,
            })

        records.sort(key=lambda r: r["upvotes"], reverse=True)
        return json.dumps(records, ensure_ascii=False) if records else "NO RESULTS"
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


@tool
def hf_search_papers(query: str, limit: int = 10) -> str:
    """Search Hugging Face papers by topic. Returns a JSON list of
    {id, url, published, title, summary, upvotes, github, stars}."""
    try:
        clean_query = query.strip()
        if not clean_query:
            return "NO RESULTS"

        limit_clamped = max(1, min(limit, 50))
        params = {"q": clean_query, "limit": limit_clamped}

        def _call():
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(HF_SEARCH_URL, params=params)
                resp.raise_for_status()
                return resp.json()

        items = with_retry(_call, attempts=5, base=1.0, cap=30.0)
        if not isinstance(items, list) or not items:
            return "NO RESULTS"

        records = []
        for item in items:
            if not isinstance(item, dict):
                continue
            paper = item.get("paper") if isinstance(item.get("paper"), dict) else item
            pid = paper.get("id") or item.get("id")
            if not pid:
                continue

            title = " ".join(str(paper.get("title") or item.get("title") or "").split())
            raw_summary = paper.get("ai_summary") or item.get("ai_summary") or paper.get("summary") or item.get("summary") or ""
            summary = " ".join(str(raw_summary).split())[:600]
            published = str(paper.get("publishedAt") or item.get("publishedAt") or "")[:10]
            upvotes = paper.get("upvotes") or item.get("upvotes") or 0
            github = paper.get("githubRepo") or item.get("githubRepo") or ""
            stars = paper.get("githubStars") or item.get("githubStars") or 0

            records.append({
                "id": str(pid),
                "url": f"https://huggingface.co/papers/{pid}",
                "published": published,
                "title": title,
                "summary": summary,
                "upvotes": int(upvotes) if isinstance(upvotes, (int, float)) else 0,
                "github": str(github) if github else "",
                "stars": int(stars) if isinstance(stars, (int, float)) else 0,
            })

        return json.dumps(records, ensure_ascii=False) if records else "NO RESULTS"
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


# ---- TODO 4: web search / fetch through the Exa MCP endpoint ----
def _call_exa_mcp(tool_name: str, arguments: dict) -> str:
    key = (os.getenv("EXA_API_KEY") or "").strip()
    url = f"{EXA_URL}?exaApiKey={key}" if key else EXA_URL
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    def _call():
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 429:
                ra = resp.headers.get("Retry-After")
                raise RetryableError("Exa rate limited (HTTP 429)", retry_after=float(ra) if ra else 5.0)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                data_lines = [line[5:].strip() for line in resp.text.splitlines() if line.startswith("data:")]
                if not data_lines:
                    raise ValueError("Empty SSE stream from Exa")
                data = json.loads(data_lines[-1])
            else:
                data = resp.json()

            if not isinstance(data, dict):
                raise ValueError("Unexpected non-dict response from Exa")

            if "error" in data:
                err = data["error"]
                err_msg = err.get("message") if isinstance(err, dict) else str(err)
                if "rate limit" in err_msg.lower() or "too many requests" in err_msg.lower():
                    raise RetryableError(f"Exa rate limited: {err_msg}", retry_after=10.0)
                raise ValueError(f"Exa MCP error: {err_msg}")

            result = data.get("result", {})
            meta = result.get("_meta", {})
            if meta.get("rate_limited") or "rate limit" in str(meta).lower():
                raise RetryableError(f"Exa rate limit flag in _meta: {meta}", retry_after=10.0)

            content_items = result.get("content", [])
            text_parts = [
                item.get("text", "")
                for item in content_items
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            full_text = "\n\n".join(text_parts).strip()

            lower_text = full_text.lower()
            if "rate limit" in lower_text and ("exceeded" in lower_text or "too many requests" in lower_text or "hit exa's free" in lower_text):
                raise RetryableError("Exa rate limit notice in content text", retry_after=10.0)

            return full_text

    return with_retry(_call, attempts=5, base=2.0, cap=60.0)


@tool
def web_search(query: str, objective: str = "", num_results: int = 5) -> str:
    """Search the web (Exa). Describe the ideal page in natural language. Returns clean text of the top results with URLs."""
    try:
        clean_query = query.strip()
        if not clean_query:
            return "NO RESULTS"
        clean_objective = objective.strip() or f"find comprehensive survey papers and articles on {clean_query}"
        num_clamped = max(1, min(num_results, 10))

        args = {
            "query": clean_query,
            "objective": clean_objective,
            "numResults": num_clamped,
        }
        text = _call_exa_mcp("web_search_exa", args)
        if not text:
            return "NO RESULTS"
        return text
    except Exception as exc:
        return _redact_key(f"ERROR: {type(exc).__name__}: {exc}")


@tool
def web_fetch(url: str) -> str:
    """Read the full content of one web page (e.g. an arXiv abstract page) as markdown. Long pages are truncated."""
    try:
        clean_url = url.strip()
        if not clean_url:
            return "NO RESULTS"
        args = {"urls": [clean_url]}
        text = _call_exa_mcp("web_fetch_exa", args)
        if not text:
            return "NO RESULTS"
        return text[:12000]
    except Exception as exc:
        return _redact_key(f"ERROR: {type(exc).__name__}: {exc}")


# ---- TODO 5: registry (the researcher subagent gets exactly these) ----
SOURCE_TOOLS = [arxiv_search, hf_daily_papers, hf_search_papers, web_search, web_fetch]


if __name__ == "__main__":
    for name, fn, args in [
        ("arxiv_search", arxiv_search, {"query": "world model", "max_results": 3}),
        ("hf_daily_papers", hf_daily_papers, {"limit": 20}),
        ("hf_search_papers", hf_search_papers, {"query": "world model", "limit": 3}),
        ("web_search", web_search, {"query": "survey paper on world models", "num_results": 2}),
        ("web_fetch", web_fetch, {"url": "https://arxiv.org/abs/1803.10122"}),
    ]:
        try:
            print(f"== {name}\n{fn.invoke(args)[:400]}\n")
        except NotImplementedError as exc:
            print(f"== {name}: not implemented yet ({exc})\n")
