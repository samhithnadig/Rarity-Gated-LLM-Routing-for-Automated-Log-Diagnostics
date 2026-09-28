# pr-buddy Evaluation: Synthetic Contributor Trajectory

This directory contains a synthetic sequence of 6 pull requests from a single
contributor persona ("Alex"), built against a small real Python library
(`textkit/`) with a real git history. Each PR diff is a genuine `git diff`
output, so it can be fed directly into pr-buddy's ingestion pipeline
(`github_ingest.py`) exactly as a real PR would be.

## Purpose

Test whether pr-buddy's feedback on PR #4 changes when it has memory of
PR #1 (same mistake type, different function) versus when memory is wiped
between sessions. This is the core load-bearing-memory ablation for the
evaluation section of the paper.

## The trajectory

| PR | File | Mistake introduced | Role |
|----|------|---------------------|------|
| 1 | `pr1_mutable_default.diff` | Mutable default argument (`merge_options`) | **First occurrence** — establishes memory |
| 2 | `pr2_missing_docstring.diff` | Missing docstring (`capitalize_words`) | Distractor |
| 3 | `pr3_missing_tests.diff` | No test added (`strip_punctuation`) | Distractor |
| 4 | `pr4_mutable_default_repeat.diff` | Mutable default argument again (`build_config`) | **Recall target** — does feedback reference PR #1? |
| 5 | `pr5_bare_except.diff` | Bare `except:` (`safe_int`) | Distractor |
| 6 | `pr6_missing_type_hints.diff` | Missing type hints (`slugify`) | Distractor |

The base repo (`textkit/`, pre-PR#1) establishes the convention every PR
violates: existing functions are typed, documented, and tested.

Three distractor PRs sit between PR #1 and PR #4 so a recall hit in PR #4's
feedback isn't trivially explained by adjacency — pr-buddy has to actually
retain and retrieve the specific mistake type across unrelated intervening
sessions.

## How to run the evaluation

1. **Memory condition:** feed PRs 1→6 into pr-buddy's `coach.py` in order,
   in a single persistent session (memory intact throughout).
2. **Control condition:** re-run the identical sequence, but wipe memory
   between each session (your existing `demo.py` control-run logic).
3. **Compare feedback on PR #4** across both conditions. Record, for each:
   - Does the feedback explicitly reference the earlier mutable-default
     mistake from PR #1? (binary, hand-coded)
   - Any language shift (generic vs. personalized — e.g. "you did this
     before" vs. a first-time explanation)
4. Repeat for a second persona/trajectory if you want more than n=1 before
   writing up results — even a second run strengthens the claim
   considerably.

## Notes for the paper

- This is a synthetic, small-n proof-of-concept ablation, not a user study —
  state that explicitly in the limitations section rather than overclaiming.
- Keep the raw before/after feedback transcripts from both conditions; a
  side-by-side excerpt is likely the single most persuasive artifact in the
  evaluation section, independent of any aggregate metric.
