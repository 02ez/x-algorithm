# x-publish-lint

Deterministic, rules-based linter for X/Twitter draft posts. **Advisory only** — never auto-publishes, never calls the X API, never uses an LLM, and never performs network I/O at runtime.

## Scope and hard limits (v1)

- No LLMs, no agents, no LangGraph.
- No X/Twitter API access. No OAuth. No account mutation.
- No auto-posting and no scheduling. The tool only reads local files and prints a report.
- No outbound network I/O. All rules are pure-Python regex/heuristic checks.
- All policy is data-driven via TOML configs and pluggable rule packs.

## Install

From the repo root (editable dev install):

```bash
python -m pip install -e "tools/x-publish-lint[dev]"
```

As a wheel (works anywhere, no env vars needed):

```bash
python -m build --wheel tools/x-publish-lint
python -m pip install tools/x-publish-lint/dist/x_publish_lint-0.1.0-py3-none-any.whl
x-publish-lint list-rules
x-publish-lint audit draft.md -f json
```

Wheel installs ship `configs/default.toml` as package data, so the CLI works from any directory without `X_PUBLISH_LINT_ROOT`. Client overrides still require an external `configs/clients/<client>.toml` and a resolvable tool root (set `X_PUBLISH_LINT_ROOT`).

Requires Python 3.11+ (uses stdlib `tomllib`).

## CLI

```bash
x-publish-lint list-rules
x-publish-lint audit path/to/draft.md -f json
x-publish-lint audit path/to/draft.md -f markdown --fail-on high
x-publish-lint scorecard path/to/draft.md --out reports/scorecard.md
```

### `audit`
- `--format / -f`: `json` (default), `markdown`, `md`, or `csv`.
- `--client / -c`: load `configs/clients/<client>.toml` overrides.
- `--fail-on`: exit non-zero when risk level meets/exceeds threshold (`low|medium|high|critical|none`). Default: `critical`.

### `scorecard`
Always emits Markdown. Use `--out` to write to a file (parent directories are created automatically).

### `list-rules`
Prints the sorted list of registered rule IDs.

## JSON contract

```jsonc
{
  "schema_version": "1.0.0",
  "config_name": "default",
  "overall_score": 78,
  "risk_level": "low",
  "positive_signals": ["reply_likelihood", "video_view_likelihood"],
  "negative_risks": [],
  "recommendations": [],
  "findings": [
    {
      "rule_id": "engagement.reply_hook",
      "kind": "positive",
      "severity": "info",
      "signal": "reply_likelihood",
      "score_delta": 8.0,
      "message": "Open-ended question increases reply likelihood.",
      "recommendation": null
    }
  ]
}
```

## Rule packs

Nine deterministic rules across five packs:

| Pack | Rule ID | Direction |
| --- | --- | --- |
| engagement | `engagement.reply_hook` | positive / negative |
| engagement | `engagement.dwell_length` | positive / negative |
| engagement | `engagement.shareability` | positive |
| media | `media.presence` | positive / negative |
| funnel | `funnel.cta_placement` | positive / negative |
| safety | `safety.brand_safety` | negative (BLOCK) |
| negative | `negative.rage_bait` | negative |
| negative | `negative.mute_keyword` | negative |
| negative | `negative.overposting` | negative |

`safety.brand_safety` is the only rule that can directly mark a draft `CRITICAL`. Any rule that raises during execution is reported as a `BLOCK` finding with signal `rule_execution_error` (fail-closed).

## Config

Tool searches for configs at `<tool-root>/configs/`:

1. Per-client override: `configs/clients/<client>.toml`
2. Default: `configs/default.toml`

Tool root is resolved via, in order:

1. `X_PUBLISH_LINT_ROOT` environment variable
2. `<cwd>/tools/x-publish-lint` (monorepo layout)
3. The editable install location (`Path(__file__).resolve().parents[2]`)
4. If none of the above contain `configs/default.toml`, the loader falls back to the packaged default that ships inside the wheel (reported as `default (packaged)` in audit output).

The packaged fallback only provides `default.toml`. Requesting a client override (`--client foo`) without a resolvable file-based tool root raises `FileNotFoundError`.

## Tests

```bash
cd tools/x-publish-lint
python -m pip install -e ".[dev]"
ruff check .
pytest
```

`mypy` is available as a dev dependency but is **not** gated in CI. Type hints are advisory.

## CI

A GitHub Actions workflow at `.github/workflows/x-publish-lint.yml` runs the test suite plus a per-PR audit of any changed draft files under `drafts/**` or `content/**`. The workflow uses `pull_request` (never `pull_request_target`), declares `permissions: contents: read`, and only uses first-party `actions/*` actions. Scorecards are uploaded as a build artifact.
