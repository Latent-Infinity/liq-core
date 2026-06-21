# AGENT_SUMMARY — liq-core

Final summary for `liq-core`'s contribution to the
[`liq-scan-plan`](../liq-docs/plans/liq-scan-plan.md). `liq-core` is the
foundation layer and carried minimal work across this plan.

## Status

| Field | Value |
| --- | --- |
| Plan | `liq-scan-plan` |
| Visibility | Public (MIT) |
| Final phase | F+1 |
| Unresolved blockers | _None._ |

## What this plan added to liq-core

- `refactor(core): widen BatchResult.results to Sequence` at `f99ecd9`
  (Phase 0). Reason: unblocks two `ty` diagnostics in `liq-data`
  (invariant `list` would not accept narrowed subclass lists). Scope: a
  single type-annotation widening; no semantics changed.

That is the entire contribution. All other phases were `n/a` per the
plan touch map.

## Verify-final evidence

- `artifacts/phase-F/verify.txt` — `pytest --cov=liq.core` green; project
  coverage **94.98 %**. `ruff check src/ tests/` clean.

## Per-phase commits

| Phase | Commit | Capability |
| --- | --- | --- |
| 0 | `f99ecd9` | Widen `BatchResult.results` to `Sequence`. |
| F | _(this commit)_ | Verify-final captured. |
| F+1 | _(this commit)_ | AGENT_SUMMARY. |

## Out-of-scope items confirmed absent

No new public APIs, no new dependencies, no namespace changes.
