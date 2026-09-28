"""
mcp_server.py

Step 4 of the log diagnostics pipeline: expose the parser -> rarity scorer ->
LLM router pipeline as MCP tools, so any MCP-aware agent (Claude Desktop,
Claude Code, etc.) can diagnose a failed Kaggle submission log directly in
conversation instead of you running scripts by hand.

Tools exposed:
  - get_rare_events(log_text): cheap, no LLM calls — just the rarity-scored
    templates. Good for a quick "what's unusual in this log" check.
  - diagnose_log(log_text): full pipeline — rarity scoring + routed LLM
    explanations for the genuinely rare/novel lines.
  - summarize_failure(log_text): one paragraph human-readable summary,
    built from diagnose_log's output.

Requires a `corpus/` directory of past logs next to this file (see
generate_corpus.py) and GOOGLE_API_KEY in the environment for live LLM
explanations — falls back to dry-run text otherwise, same as llm_router.py.

Run:
    python3 mcp_server.py
"""

import os
import tempfile
from pathlib import Path

from mcp.server import MCPServer

from rarity_scorer import fit_corpus, score_target_log
from llm_router import classify, build_prompt, call_llm, CANNED_KNOWN_UNCOMMON

CORPUS_DIR = Path(__file__).parent / "corpus"

mcp = MCPServer("kaggle-log-diagnostics")

# Fit the corpus once at startup rather than on every tool call — the corpus
# is static between deploys, so re-fitting per-request would be wasted work.
_miner, _doc_freq, _total_logs = fit_corpus(CORPUS_DIR)


def _score_text(log_text: str) -> list:
    """Write log_text to a temp file and run it through the existing,
    already-tested scoring pipeline (which is file-path based)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write(log_text)
        temp_path = f.name
    try:
        return score_target_log(_miner, _doc_freq, _total_logs, temp_path)
    finally:
        os.unlink(temp_path)


@mcp.tool()
def get_rare_events(log_text: str) -> str:
    """Score a Kaggle notebook log's lines by how rare each pattern is
    relative to a corpus of past runs, without calling any LLM. Returns
    the templates ranked from most to least unusual. Use this for a quick,
    free check of what's unusual in a log before requesting full diagnosis.
    """
    scored = _score_text(log_text)
    lines = [f"Corpus: {_total_logs} past logs, {len(_miner.drain.clusters)} known templates.\n"]
    for r in scored[:15]:
        seen = "never seen before" if r["corpus_doc_freq"] == 0 else f"seen in {r['corpus_doc_freq']}/{r['corpus_size']} past runs"
        lines.append(f"[rarity {r['rarity']:.2f}] (line {r['first_line']}, {seen}): {r['template']}")
    return "\n".join(lines)


@mcp.tool()
def diagnose_log(log_text: str) -> str:
    """Run the full diagnostics pipeline on a Kaggle notebook log: score
    every line's rarity against the corpus of past runs, then get an LLM
    explanation for the genuinely rare/novel lines (cost-controlled — only
    the rare ones get an LLM call, routine lines are skipped or given a
    canned message). Returns a routed, explained report.
    """
    scored = _score_text(log_text)
    dry_run = "GOOGLE_API_KEY" not in os.environ
    out = []

    for record in scored:
        route = classify(record)
        if route == "llm":
            prompt = build_prompt(record)
            explanation = call_llm(prompt, dry_run=dry_run)
            out.append(f"[LLM] line {record['first_line']}: {record['template']}\n  -> {explanation}")
        elif route == "canned":
            msg = CANNED_KNOWN_UNCOMMON.format(df=record["corpus_doc_freq"], total=record["corpus_size"])
            out.append(f"[KNOWN] line {record['first_line']}: {record['template']}\n  -> {msg}")

    if not out:
        return "No unusual patterns found — this log matches routine past runs."
    return "\n\n".join(out)


@mcp.tool()
def summarize_failure(log_text: str) -> str:
    """Produce a one-paragraph, human-readable summary of what likely went
    wrong in a Kaggle notebook run, based on the rarest/most novel lines
    found in the log. Good for a quick top-line answer rather than a full
    line-by-line report — use diagnose_log for the detailed version.
    """
    scored = _score_text(log_text)
    novel = [r for r in scored if r["rarity"] >= 0.9]

    if not novel:
        return "This log doesn't contain any unusual patterns relative to past runs — looks like a routine run."

    dry_run = "GOOGLE_API_KEY" not in os.environ
    top = novel[0]
    prompt = build_prompt(top)
    explanation = call_llm(prompt, dry_run=dry_run)

    other_count = len(novel) - 1
    extra = f" ({other_count} other unusual line{'s' if other_count != 1 else ''} also detected.)" if other_count else ""
    return f"Most likely cause: {explanation}{extra}"


if __name__ == "__main__":
    mcp.run()
