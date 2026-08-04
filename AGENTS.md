# Instructions for LLM Agents

Read the following files before working on this repository:

- [README.md](README.md) — project overview, how to add tools, development
  workflow, testing, and releasing
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to report issues, submit pull
  requests, commit guidelines, and review process

## Single-File Verification

Lint and type-check individual files without a full build:

```sh
# Python
uv run ruff check path/to/file.py
uv run ruff format --check path/to/file.py
uv run pyright path/to/file.py

# Shell
shellcheck path/to/file.sh
```

## Pip Build Dependencies

Duplicate package entries in `deps/pip/requirements-build.txt` are intentional.
Do not deduplicate them. See the note in the [Pip Packages](README.md#pip-packages)
section of the README.
