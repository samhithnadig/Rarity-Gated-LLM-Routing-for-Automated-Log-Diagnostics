"""
llm_router.py

Step 3 of the log diagnostics pipeline: given rarity-scored templates from
rarity_scorer.py, decide which ones are worth spending an LLM call on to
explain, and which can be handled with a cheap canned message. This is the
cost-control layer — the whole point of scoring rarity first is so the LLM
only sees the handful of lines that actually need explaining, not the
entire log.

Routing policy (simple, explicit thresholds — tune as needed):
  - rarity >= 0.9  OR  corpus_doc_freq == 0   -> route to LLM (likely novel issue)
  - 0.6 <= rarity < 0.9                        -> canned "known-uncommon" message
  - rarity < 0.6                               -> skip entirely (routine output)

Usage:
    python3 llm_router.py corpus/ path/to/target_log.log
    (requires GOOGLE_API_KEY in the environment to make real calls — get a
     free key at https://aistudio.google.com/apikey; otherwise runs in
     dry-run mode and prints what would be sent)
"""

import os
import sys
from pathlib import Path

from rarity_scorer import fit_corpus, score_target_log

ROUTE_TO_LLM_RARITY = 0.9
CANNED_TIER_RARITY = 0.6

CANNED_KNOWN_UNCOMMON = (
    "This is a known-but-uncommon pattern (seen in {df}/{total} past runs). "
    "Likely not a new issue — check past runs with the same message for the fix that worked before."
)


def classify(record: dict) -> str:
    """Return 'llm', 'canned', or 'skip' for a scored template record."""
    if record["rarity"] >= ROUTE_TO_LLM_RARITY:
        return "llm"
    if record["rarity"] >= CANNED_TIER_RARITY:
        return "canned"
    return "skip"


def build_prompt(record: dict) -> str:
    """Build the explanation prompt sent to Claude for a routed (rare) template."""
    return (
        "You are diagnosing a failed Kaggle notebook submission. Below is a log line/template "
        "that is statistically rare or never-before-seen across the user's past submission logs. "
        "In 2-3 sentences: (1) explain what likely caused this, and (2) suggest one concrete next "
        "step to fix or investigate it. Be specific and concise — no preamble.\n\n"
        f"Log line (occurred {record['occurrences_in_target']}x in this run, "
        f"seen in {record['corpus_doc_freq']}/{record['corpus_size']} past runs):\n"
        f"{record['template']}"
    )


def call_llm(prompt: str, dry_run: bool, max_retries: int = 4) -> str:
    """Call Gemini for an explanation, or return the prompt itself in dry-run mode.

    Retries on transient server errors (503 "high demand") with a short
    backoff, and on rate-limit errors (429, free tier is 5 req/min) with a
    longer ~60s backoff — a single overloaded or rate-limited request
    shouldn't kill the whole batch.
    """
    if dry_run:
        return f"[DRY RUN — no GOOGLE_API_KEY set. Prompt that would be sent:]\n{prompt}"

    import re
    import time
    from google import genai
    from google.genai import errors as genai_errors

    client = genai.Client()  # reads GOOGLE_API_KEY from env

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            return response.text
        except genai_errors.ClientError as e:
            is_rate_limit = getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e)
            if not is_rate_limit:
                return f"[LLM call failed — {e}]"
            if attempt == max_retries:
                return f"[LLM call failed after {max_retries} rate-limit retries — {e}]"
            # Google's 429 response includes a suggested retryDelay (e.g. "29s") — use it
            # plus a small buffer instead of guessing, so we wait exactly as long as needed.
            wait_seconds = 65  # safe default if we can't parse the suggested delay
            match = re.search(r"'retryDelay':\s*'(\d+)s'", str(e))
            if match:
                wait_seconds = int(match.group(1)) + 5
            time.sleep(wait_seconds)
        except genai_errors.ServerError as e:
            if attempt == max_retries:
                return f"[LLM call failed after {max_retries} attempts — {e}]"
            time.sleep(2 ** attempt)  # 2s, 4s, 8s backoff


def run_pipeline(corpus_dir: Path, target_log: str):
    dry_run = "GOOGLE_API_KEY" not in os.environ

    miner, doc_freq, total_logs = fit_corpus(corpus_dir)
    scored = score_target_log(miner, doc_freq, total_logs, target_log)

    llm_count, canned_count, skip_count = 0, 0, 0

    print(f"Fit corpus of {total_logs} logs -> {len(miner.drain.clusters)} unique templates.")
    print(f"Mode: {'DRY RUN (no API key)' if dry_run else 'LIVE (calling Claude)'}\n")
    print("=" * 70)

    for record in scored:
        route = classify(record)
        if route == "llm":
            llm_count += 1
            print(f"\n[ROUTE: LLM]  rarity={record['rarity']}  line {record['first_line']}")
            print(f"  {record['template']}")
            prompt = build_prompt(record)
            explanation = call_llm(prompt, dry_run=dry_run)
            print(f"  -> {explanation}\n")
        elif route == "canned":
            canned_count += 1
            msg = CANNED_KNOWN_UNCOMMON.format(df=record["corpus_doc_freq"], total=record["corpus_size"])
            print(f"\n[ROUTE: CANNED]  rarity={record['rarity']}  line {record['first_line']}")
            print(f"  {record['template']}")
            print(f"  -> {msg}")
        else:
            skip_count += 1

    print("\n" + "=" * 70)
    print(
        f"Summary: {llm_count} routed to LLM, {canned_count} canned messages, "
        f"{skip_count} skipped as routine (out of {len(scored)} unique templates)."
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 llm_router.py <corpus_dir> <target_log_path>")
        sys.exit(1)

    run_pipeline(Path(sys.argv[1]), sys.argv[2])
