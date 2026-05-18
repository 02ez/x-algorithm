# x-publish-lint Roadmap

## Follow-up: package config files for non-editable installs

Currently v1 is repo/tooling oriented and relies on `X_PUBLISH_LINT_ROOT`, monorepo cwd, or editable install layout.

Before publishing to PyPI or using outside the repo, package `configs/default.toml` as package data or move defaults into code with override support.

## Acceptance criteria

- `pip install dist/*.whl`
- `x-publish-lint list-rules`
- `x-publish-lint audit draft.md -f json`
- Works outside repo root without `X_PUBLISH_LINT_ROOT`
