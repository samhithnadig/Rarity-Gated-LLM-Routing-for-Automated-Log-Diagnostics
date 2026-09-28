# Rarity-Gated LLM Routing for Automated Log Diagnostics

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22902744.svg)](https://doi.org/10.5281/zenodo.22902744)

A log diagnostics pipeline that separates **detection** from **explanation**.
Instead of sending a whole failed log to an LLM, it scores every line by how
rare its template is across a corpus of past logs, and only spends an LLM call
on lines that are genuinely novel. Known failures get a cheap canned message,
and routine lines are skipped. The pipeline is also exposed as
[MCP](https://modelcontextprotocol.io) tools, so an assistant like Claude
Desktop or Claude Code can call it mid-conversation.

Paper: *Rarity-Gated LLM Routing for Automated Log Diagnostics* (2026),
https://doi.org/10.5281/zenodo.22902744

## How it works

```
raw log ──► log_parser.py ──► rarity_scorer.py ──► llm_router.py ──► report
            (Drain3 templates)  (document-frequency    (rare  -> LLM explanation
                                 rarity vs. corpus)     mid   -> canned message
                                                        low   -> skipped)
                                        └──────────► mcp_server.py (3 MCP tools)
```

| Rarity score | Action |
|---|---|
| >= 0.9 (or template never seen) | Route to LLM for a short explanation |
| 0.6 - 0.9 | Cheap canned message pointing at precedent |
| < 0.6 | Skip, routine output |

Rarity is `1 - (fraction of past logs containing this template)`. It is
deliberately simple and auditable rather than a learned model.

## Files

| File | Purpose |
|---|---|
| `log_parser.py` | Cleans log lines and mines templates with Drain3 |
| `rarity_scorer.py` | Fits templates across a corpus, scores a new log's lines |
| `llm_router.py` | Threshold routing, LLM call, retry/backoff for 503 and 429 (honors the provider's suggested `retryDelay`) |
| `mcp_server.py` | Exposes `get_rare_events`, `diagnose_log`, `summarize_failure` |
| `generate_corpus.py` | Builds the synthetic 16-log evaluation corpus (seed = 7) |
| `batch_eval.py` | Leave-one-out evaluation over the corpus, writes `eval_results.md` |
| `test_tools.py` | Tests for the MCP tools |
| `eval_results.md` | Full evaluation transcript with every LLM explanation |

## Setup

```bash
git clone https://github.com/samhithnadig/Rarity-Gated-LLM-Routing-for-Automated-Log-Diagnostics.git
cd Rarity-Gated-LLM-Routing-for-Automated-Log-Diagnostics
python3 -m venv venv
source venv/bin/activate
pip install drain3 google-genai mcp
```

Generate the corpus (10 healthy, 3 known CUDA-OOM, 3 novel failures):

```bash
python3 generate_corpus.py
```

## Run the evaluation

Without an API key it runs in **dry-run** mode: routing decisions are computed
and the prompts that *would* be sent are printed, at no cost.

```bash
python3 batch_eval.py
```

For live LLM explanations, set your key in the shell (never commit it):

```bash
export GOOGLE_API_KEY=your-key-here
python3 batch_eval.py
```

Each log is scored against a corpus that **excludes itself** (leave-one-out),
so a log can never trivially match its own templates.

## Run the MCP server

```bash
python3 mcp_server.py
```

Then register it with any MCP-aware client. Tools:

- `get_rare_events(log_text)`: free, no LLM calls, returns the rare lines
- `diagnose_log(log_text)`: full routed report
- `summarize_failure(log_text)`: one-paragraph verdict

## Results (16-log corpus)

- **Cost control:** all 13 logs without a novel failure (10 healthy, 3 known
  OOM) triggered **0** LLM calls. Total: 15 LLM calls, 24 canned messages,
  195 skipped lines.
- **Explanation accuracy (hand-coded):** 10/15 LLM explanations (66.7%)
  identified the true root cause.
- **Cold-start finding:** a bare separator line that caused
  out-of-memory hallucinations in the first 15-log run stopped being routed to
  the LLM at all once a third novel log gave it precedent in the corpus. No
  special-casing was needed.
- **Remaining errors** are hedging between causes and generic non-answers on
  lines that do contain real content.

See the paper for the full method, methodology and limitations.

## Limitations

- The corpus is small and synthetic (16 logs), not longitudinal real-world data.
- Evaluated with a single LLM provider (Gemini).
- The method is domain-agnostic, but the evaluation corpus is Kaggle notebook
  logs only. Other log domains (CI/CD, infrastructure) are untested.
- One example per novel failure type is not enough to claim the cold-start
  effect holds for every kind of structural line.

## Citation

```bibtex
@techreport{nadig2026rarity,
  title  = {Rarity-Gated LLM Routing for Automated Log Diagnostics},
  author = {Nadig, Samhith},
  year   = {2026},
  doi    = {10.5281/zenodo.22902744},
  url    = {https://doi.org/10.5281/zenodo.22902744}
}
```

## License

Add a license file before publishing (MIT is a common default for portfolio
code).
