# Scripts

Python scripts for artifact compression in the Reloaded Publish Action.

## Quick Start

```bash
# Run tests (creates venv automatically)
python scripts/run-tests.py
```

## Manual Setup (for VSCode debugging)

```bash
# Create venv once
python scripts/setup-venv.py

# Run tests without venv wrapper
python scripts/run-tests.py --no-venv
```

After running `setup-venv.py`, configure VSCode to use `scripts/.venv/bin/python` as the interpreter.

## Compression Script

The `compress-artifacts.py` script compresses artifact directories into archives:

```bash
python scripts/compress-artifacts.py \
  --artifacts-dir artifacts \
  --output-dir compressed \
  --tool zip \
  --groups 'c-library: [c-library-linux, c-library-windows]'
```

Options:
- `--tool`: `zip` (default) or `7z`
- `--groups`: YAML config for grouping directories into single archives
- `--args`: Extra arguments passed to the compression tool

### Grouping Configuration

Groups can be defined as explicit lists or using glob patterns:

```yaml
# Explicit list
c-library: [c-library-linux, c-library-windows, c-library-macos]

# Pattern matching - single string syntax
symbols:
  patterns: "*.symbols"

# Multiple patterns (union - matches ANY) - list syntax
binaries:
  patterns:
    - "*-x64"
    - "*-arm64"
  excludes:
    - "*.symbols"

# Mixed - single pattern (string), single exclude (string)
non-symbols:
  patterns: "*"
  excludes: "*.symbols"
```

The `patterns` and `excludes` keys accept either a single string or a list of strings.
Directories matching ANY pattern are included.
