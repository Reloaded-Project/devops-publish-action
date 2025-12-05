# Scripts

Python scripts for artifact compression in the Reloaded Publish Action.

## Quick Start

```bash
# Run tests (creates venv automatically)
python scripts/run-tests.py
```

## Debugging with VS Code

### Setup

1. Create the virtual environment:
   ```bash
   python scripts/setup-venv.py
   ```

2. Select the interpreter in VS Code:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Type "Python: Select Interpreter"
   - Choose `scripts/.venv/bin/python` (or `scripts/.venv/Scripts/python.exe` on Windows)

### Debug Configurations

Two launch configurations are provided in `.vscode/launch.json`:

- **Run Tests**: Runs the pytest test suite with verbose output. Set breakpoints in test files or source code to debug.
- **Compress Artifacts (Example)**: Runs the compression script against sample test data. Modify the `args` array to test different scenarios.

To debug: set breakpoints in the code, then press `F5` or use the Run and Debug panel to select a configuration.

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

Groups can be defined as explicit lists or using glob patterns with `patterns` and `excludes` keys.

See [Artifact Groups Examples](../README.MD#artifact-groups-examples) in the main README for full documentation.

### Flattening Directories

The `flattens` option places files from matched directories directly at the archive root instead of preserving directory structure.

See [Artifact Groups Examples](../README.MD#artifact-groups-examples) in the main README for full documentation.
