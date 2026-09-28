"""
log_parser.py

Step 1 of the log diagnostics pipeline: turn raw Kaggle notebook logs into
Drain3 templates (clustered patterns), stripping the per-line timing/line-
number noise first so the miner clusters on message content, not metadata.

Usage:
    python3 log_parser.py path/to/log_file.log
"""

import re
import sys
from pathlib import Path

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

# Kaggle notebook log lines look like:
#   "20.6s 12 0.00s - message text"        (timed message)
#   "70.4s 22 ---> 87     outputs = ..."   (raw traceback line, no delta/dash)
#   "118.0s 29"                            (blank / table line)
#
# Strip the leading "[cum_time]s [line_num] " prefix, then optionally strip
# a "[delta_time]s - " prefix from what remains. What's left is the actual
# message content Drain3 should cluster on.
LEADING_PREFIX = re.compile(r"^\d+(?:\.\d+)?s\s+\d+\s?")
DELTA_PREFIX = re.compile(r"^\d+(?:\.\d+)?s\s+-\s+")


def clean_line(raw_line: str) -> str:
    """Strip Kaggle's timing/line-number metadata, leaving the log message."""
    line = raw_line.rstrip("\n")
    line = LEADING_PREFIX.sub("", line, count=1)
    line = DELTA_PREFIX.sub("", line, count=1)
    return line.strip()


def build_template_miner() -> TemplateMiner:
    """Configure a Drain3 TemplateMiner with sensible defaults for this format."""
    config = TemplateMinerConfig()
    config.load(str(Path(__file__).parent / "drain3.ini")) if (
        Path(__file__).parent / "drain3.ini"
    ).exists() else None
    # Reasonable defaults if no config file is present:
    config.drain_sim_th = 0.4
    config.drain_depth = 4
    config.drain_max_children = 100
    config.drain_max_clusters = 1024
    return TemplateMiner(config=config)


def parse_log(path: str):
    """Run every line of a log file through Drain3 and return the miner + per-line records."""
    miner = build_template_miner()
    records = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i, raw_line in enumerate(f, start=1):
            message = clean_line(raw_line)
            if not message:
                continue  # skip blank lines — no signal for the parser
            result = miner.add_log_message(message)
            records.append(
                {
                    "line_no": i,
                    "message": message,
                    "cluster_id": result["cluster_id"],
                    "template": result["template_mined"],
                    "change_type": result["change_type"],  # none / cluster_created / cluster_template_changed
                }
            )
    return miner, records


def print_summary(miner: TemplateMiner, records: list):
    print(f"Parsed {len(records)} non-blank lines into {len(miner.drain.clusters)} templates.\n")

    print("=== Discovered templates (sorted by frequency) ===")
    clusters = sorted(miner.drain.clusters, key=lambda c: c.size, reverse=True)
    for cluster in clusters:
        print(f"  [{cluster.size:>3}x] id={cluster.cluster_id}  {cluster.get_template()}")

    print("\n=== Rare templates (size == 1) — likely candidates for the rarity scorer ===")
    rare = [c for c in clusters if c.size == 1]
    if not rare:
        print("  (none — every line matched a repeated pattern)")
    for cluster in rare:
        matching = [r for r in records if r["cluster_id"] == cluster.cluster_id]
        line_no = matching[0]["line_no"] if matching else "?"
        print(f"  line {line_no}: {cluster.get_template()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 log_parser.py <path_to_log_file>")
        sys.exit(1)

    log_path = sys.argv[1]
    miner, records = parse_log(log_path)
    print_summary(miner, records)
