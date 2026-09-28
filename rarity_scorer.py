"""
rarity_scorer.py

Step 2 of the log diagnostics pipeline: fit Drain3 across a corpus of past
logs to learn which templates are "normal" (seen in many past runs) vs.
rare (seen in few, or never before). Then score a new/target log's lines
by rarity, so the LLM router (step 3) only spends tokens explaining the
genuinely unusual lines — not routine progress output.

Rarity is document frequency based: how many corpus logs contain this
template at least once (not raw occurrence count), so a template that
appears 3 times in one repeated-failure log doesn't look "common" just
because it repeats within a single run.

Usage:
    python3 rarity_scorer.py corpus/ path/to/target_log.log
"""

import sys
from pathlib import Path

from log_parser import build_template_miner, clean_line


def fit_corpus(corpus_dir: Path):
    """Fit one shared TemplateMiner across every log in corpus_dir.

    Returns the fitted miner plus a dict of cluster_id -> document frequency
    (number of distinct corpus logs the template appeared in at least once).
    """
    miner = build_template_miner()
    doc_freq = {}
    log_files = sorted(corpus_dir.glob("*.log"))

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


def score_target_log(miner, doc_freq: dict, total_logs: int, target_path: str):
    """Score each unique template in the target log by corpus-wide rarity.

    rarity = 1 - (doc_freq / total_logs) for templates seen before.
    rarity = 1.0 for templates never seen in the corpus at all (max rarity).
    """
    seen_templates = {}  # cluster_id or None -> (template_text, first_line_no, occurrence_count)

    with open(target_path, "r", encoding="utf-8", errors="replace") as f:
        for i, raw_line in enumerate(f, start=1):
            message = clean_line(raw_line)
            if not message:
                continue
            cluster = miner.match(message)
            if cluster is None:
                key = ("UNSEEN", message)  # never matched anything in corpus
                template_text = message
            else:
                key = ("SEEN", cluster.cluster_id)
                template_text = cluster.get_template()

            if key not in seen_templates:
                seen_templates[key] = [template_text, i, 0]
            seen_templates[key][2] += 1

    scored = []
    for key, (template_text, first_line, count) in seen_templates.items():
        if key[0] == "UNSEEN":
            rarity = 1.0
            df = 0
        else:
            df = doc_freq.get(key[1], 0)
            rarity = 1.0 - (df / total_logs)
        scored.append(
            {
                "template": template_text,
                "first_line": first_line,
                "occurrences_in_target": count,
                "corpus_doc_freq": df,
                "corpus_size": total_logs,
                "rarity": round(rarity, 3),
            }
        )

    scored.sort(key=lambda r: r["rarity"], reverse=True)
    return scored


def print_report(scored: list, top_k: int = 10):
    print(f"=== Top {top_k} rarest templates (candidates for LLM routing) ===\n")
    for r in scored[:top_k]:
        seen_note = "NEVER SEEN IN CORPUS" if r["corpus_doc_freq"] == 0 else f"seen in {r['corpus_doc_freq']}/{r['corpus_size']} corpus logs"
        print(f"  rarity={r['rarity']:.3f}  (line {r['first_line']}, x{r['occurrences_in_target']} in this log, {seen_note})")
        print(f"    {r['template']}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 rarity_scorer.py <corpus_dir> <target_log_path>")
        sys.exit(1)

    corpus_dir = Path(sys.argv[1])
    target_log = sys.argv[2]

    miner, doc_freq, total_logs = fit_corpus(corpus_dir)
    print(f"Fit corpus of {total_logs} logs -> {len(miner.drain.clusters)} unique templates.\n")

    scored = score_target_log(miner, doc_freq, total_logs, target_log)
    print_report(scored)
