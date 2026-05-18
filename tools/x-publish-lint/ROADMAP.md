# x-publish-lint Roadmap

## Done in v1.1: package default config for non-editable installs

`configs/default.toml` is shipped inside the wheel as package data at
`x_publish_lint.configs.default.toml`. The loader resolves a file-based
search root first (env var, cwd, editable install) and falls back to the
packaged resource via `importlib.resources` when none is available. Client
overrides (`--client <name>`) still require an external `configs/clients/<name>.toml`
and a resolvable tool root.

Verified acceptance:

- `python -m build --wheel tools/x-publish-lint` produces a wheel containing `x_publish_lint/configs/default.toml`.
- `pip install dist/x_publish_lint-0.1.0-py3-none-any.whl` in a fresh venv outside the repo.
- `x-publish-lint list-rules` prints 9 sorted rule IDs.
- `x-publish-lint audit draft.md -f json` runs without `X_PUBLISH_LINT_ROOT` and reports `config_name: "default (packaged)"`.

## Next

- Calibration dataset format (synthetic + real exemplars, deterministic labels).
- Outcome ingestion (post-publish results join keyed by draft hash).
- Per-client weight tuning workflow.
- Agent layer (last; behind a feature flag, still no network at runtime).
