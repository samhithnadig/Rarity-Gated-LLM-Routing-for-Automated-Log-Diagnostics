"""
batch_eval.py

Runs the full diagnostics pipeline (rarity scoring + LLM routing) over
every log in corpus/, using leave-one-out fitting: when scoring log X,
the corpus is fit on the other 14 logs, not on all 15. Scoring a log
against a corpus that includes itself would trivially match its own
template (data leakage) — leave-one-out avoids that and gives an honest
read of how the rarity scorer generalizes to a log it hasn't seen.

Ground truth failure type is inferred from each file's name prefix
(healthy_ / cuda_oom_ / keyerror_novel_ / timeout_novel_), since that's
how generate_corpus.py names them.

Output: writes eval_results.md with, for every log:
  - routing summary (N routed to LLM / N canned / N skipped)
  - the full text of every LLM explanation received
  - a blank "correct?" column for you to hand-code against the known
    ground-truth failure

Usage:
    python3 batch_eval.py
    (requires GOOGLE_API_KEY in the environment for live explanations;
     runs in dry-run mode otherwise — still useful for checking routing
     counts without spending any quota)
"""

import os
import time
from pathlib import Path

from log_parser import build_template_miner, clean_line
from rarity_scorer import score_target_log
from llm_router import classify, build_prompt, call_llm, CANNED_KNOWN_UNCOMMON

CORPUS_DIR = Path(__file__).parent / "corpus"
OUTPUT_PATH = Path(__file__).parent / "eval_results.md"


def fit_corpus_excluding(corpus_dir: Path, exclude_path: Path):
    """Same as rarity_scorer.fit_corpus, but skips one log file — used for
    leave-one-out evaluation so a log is never scored against itself."""
    miner = build_template_miner()
    doc_freq = {}
    log_files = sorted(p for p in corpus_dir.glob("*.log") if p != exclude_path)

    for log_path in log_files:
        clusters_in_this_log = set()
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                message = clean_line(raw_line)
                if not message:
                    continue
                result = miner.add_log_message(message)
                clusters_in_this_log.add(result["cluster_id"])
        for cluster_id in clusters_in_this_log:
            doc_freq[cluster_id] = doc_freq.get(cluster_id, 0) + 1

    return miner, doc_freq, len(log_files)


def ground_truth_type(filename: str) -> str:
    if filename.startswith("healthy_"):
        return "healthy (no failure)"
    if filename.startswith("cuda_oom_"):
        return "CUDA out-of-memory (known/recurring)"
    if filename.startswith("keyerror_novel_"):
        return "pandas merge KeyError (novel)"
    if filename.startswith("timeout_novel_"):
        return "network read timeout (novel)"
    if filename.startswith("valueerror_novel_"):
        return "sklearn feature-count ValueError (novel)"
    return "unknown"


def run_one_log(log_path: Path, dry_run: bool) -> dict:
    miner, doc_freq, total_logs = fit_corpus_excluding(CORPUS_DIR, log_path)
    scored = score_target_log(miner, doc_freq, total_logs, str(log_path))

    llm_results, canned_results = [], []
    llm_count = canned_count = skip_count = 0

    for record in scored:
        route = classify(record)
        if route == "llm":
            llm_count += 1
            prompt = build_prompt(record)
            explanation = call_llm(prompt, dry_run=dry_run)
            llm_results.append((record, explanation))
            if not dry_run:
                time.sleep(15)  # stay safely under free tier's 5 req/min limit
        elif route == "canned":
            canned_count += 1
            canned_results.append(record)
        else:
            skip_count += 1

    return {
        "filename": log_path.name,
        "ground_truth": ground_truth_type(log_path.name),
        "corpus_size_used": total_logs,
        "llm_count": llm_count,
        "canned_count": canned_count,
        "skip_count": skip_count,
        "llm_results": llm_results,
        "canned_results": canned_results,
    }


def write_report(results: list, dry_run: bool):
    lines = ["# Batch Evaluation Results\n"]
    lines.append(f"Mode: {'DRY RUN (no GOOGLE_API_KEY)' if dry_run else 'LIVE (Gemini)'}")
    lines.append(f"Logs evaluated: {len(results)} (leave-one-out scoring, corpus size {results[0]['corpus_size_used']} per log)\n")

    lines.append("## Summary table\n")
    lines.append("| Log | Ground truth | LLM calls | Canned | Skipped |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append(f"| {r['filename']} | {r['ground_truth']} | {r['llm_count']} | {r['canned_count']} | {r['skip_count']} |")

    total_llm = sum(r["llm_count"] for r in results)
    total_canned = sum(r["canned_count"] for r in results)
    total_skip = sum(r["skip_count"] for r in results)
    lines.append(f"\n**Totals: {total_llm} LLM calls, {total_canned} canned, {total_skip} skipped across {len(results)} logs.**\n")

    lines.append("## LLM explanations (hand-code correctness against ground truth)\n")
    for r in results:
        if not r["llm_results"]:
            continue
        lines.append(f"### {r['filename']} — ground truth: {r['ground_truth']}\n")
        for record, explanation in r["llm_results"]:
            lines.append(f"**Line {record['first_line']}** (rarity {record['rarity']}): `{record['template']}`\n")
            lines.append(f"> {explanation}\n")
            lines.append("Correct root cause? (y/n): ____\n")

    OUTPUT_PATH.write_text("\n".join(lines))
    print(f"Wrote {OUTPUT_PATH}")
    print(f"\nTotals: {total_llm} LLM calls, {total_canned} canned, {total_skip} skipped.")


def main():
    dry_run = "GOOGLE_API_KEY" not in os.environ
    log_files = sorted(CORPUS_DIR.glob("*.log"))
    print(f"Running batch eval over {len(log_files)} logs. Mode: {'DRY RUN' if dry_run else 'LIVE'}\n")

    results = []
    for i, log_path in enumerate(log_files, start=1):
        print(f"[{i}/{len(log_files)}] {log_path.name}...")
        results.append(run_one_log(log_path, dry_run=dry_run))

    write_report(results, dry_run=dry_run)


if __name__ == "__main__":
    main()