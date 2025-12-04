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
