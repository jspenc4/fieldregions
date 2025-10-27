# Development Setup

This document contains important information for working on this project.

## Python Virtual Environment

**IMPORTANT**: This project uses a Python virtual environment located in `venv/`.

### Always use the venv Python

When running Python commands or installing packages, **always use the venv binaries**:

```bash
# Correct - uses venv
venv/bin/python3 script.py
venv/bin/pip3 install package-name

# Incorrect - uses system Python
python3 script.py
pip3 install package-name
```

### Activating the venv (optional)

If you prefer to activate the venv for your shell session:

```bash
source venv/bin/activate
```

However, for scripts and one-off commands, using the full path (`venv/bin/python3`) is more reliable.

## Project Structure

- `src/cli/` - Command-line tools for potential calculation and visualization
- `lib/` - Reusable library code for potential calculations and visualization
- `output/` - Generated data files and visualizations (gitignored)
- `docs/` - Documentation and project website
- `tests/` - Test suite

## Common Commands

```bash
# Preprocess: Add hex infill for smooth coastal visualization
venv/bin/python3 src/cli/add_hex_infill.py input.csv -o input_hex.csv --spacing 30

# Calculate potentials
venv/bin/python3 src/cli/calculate_potential.py input.csv -o output.csv

# Visualize as 3D HTML
venv/bin/python3 src/cli/visualize_potential.py output.csv --type mesh

# Visualize as PNG (high quality)
venv/bin/python3 src/cli/visualize_potential.py output.csv --type mesh --png --hq

# Visualize with gradient direction coloring (for 3D printing)
venv/bin/python3 src/cli/visualize_potential.py output.csv --type mesh --color-by-gradient --hq --png

# Run tests
venv/bin/python3 -m pytest tests/
```

## Installing Dependencies

```bash
# Install a new package
venv/bin/pip3 install package-name

# Install from requirements.txt (if it exists)
venv/bin/pip3 install -r requirements.txt
```

## Notes for AI Assistants

If you're an AI helping with this project and you see this file: **always use `venv/bin/python3` and `venv/bin/pip3`**. Do not use system Python or pip.
