# Contributing to grok-geo

Thank you for considering contributing to grok-geo! This document explains how to get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/your-username/grok-geo/issues) to avoid duplicates.
2. Open a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the problem
   - Expected vs actual behavior
   - Your environment (OS, Python version)

### Suggesting Features

Open an issue with the `enhancement` label describing:
- The problem you are trying to solve
- Your proposed solution
- Alternatives you considered

### Submitting Code

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Write or update tests
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- Git

### Steps

```bash
# Clone your fork
git clone https://github.com/your-username/grok-geo.git
cd grok-geo

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dev dependencies
pip install -e ".[dev]"
```

### Optional Tools

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Project Structure

```text
skill/grok-geo/    # Skill core
  modules/                 # Pipeline module specs
  schemas/                 # JSON Schema definitions
  scripts/                 # Deterministic Python scripts
    core/                  #   Shared utilities (constants, runners, I/O)
    scoring/               #   Scoring algorithms
  templates/               # Report templates (.md.tpl)
  evals/                   # Evaluation harness
  examples/                # Offline demo inputs and runner
  references/              # Methodology and specification docs
tests/                     # Unit, integration, boundary, performance tests
devtools/                  # Upload/inspect helpers (not packaged)
scripts/                   # Build/packaging scripts
dist/                      # Release artifacts
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-new-metric` for new features
- `fix/citation-classification` for bug fixes
- `docs/update-readme` for documentation changes
- `refactor/modularize-scoring` for refactors

### Code Style

- Follow PEP 8 for Python code
- Use type hints where practical
- Keep functions focused and small
- Prefer pure functions over side-effect-heavy ones
- Add docstrings for public functions

### Commit Messages

Write clear, concise commit messages:

```
Add cross-engine citation comparison metric

Implements the comparison logic between ChatGPT, Perplexity, and
Claude citation counts. Adds corresponding JSON schema and unit tests.
```

## Testing

### Run All Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Or with make:

```bash
make test
```

### Run Specific Test Categories

```bash
# Unit tests only
python -m unittest discover -s tests/unit -p "test_*.py" -v

# Integration tests
python -m unittest discover -s tests/integration -p "test_*.py" -v

# Boundary/edge case tests
python -m unittest discover -s tests/boundary -p "test_*.py" -v
```

### Run Evals

```bash
python skill/grok-geo/evals/run_evals.py
```

### Offline Demo

```bash
python skill/grok-geo/examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep
```

### What to Test

When adding new functionality:

- Add unit tests for new functions
- Add edge cases to boundary tests
- Update eval cases if the report format changes
- Verify the offline demo still produces valid output

## Pull Request Process

1. **Ensure tests pass** before submitting.
2. **Update documentation** if your change affects usage or behavior.
3. **Update CHANGELOG.md** with a brief description of your change under an appropriate section.
4. **Keep PRs focused**: one feature or fix per PR.
5. **Write a clear PR description** explaining what changed and why.

### PR Description Template

```markdown
## What

Brief description of the change.

## Why

Motivation or link to related issue.

## How

Implementation approach (if non-obvious).

## Tests

- [ ] Unit tests added/updated
- [ ] Existing tests pass
- [ ] Eval cases updated (if applicable)
```

### Review Process

- At least one review is required before merge.
- CI must pass (tests, linting).
- Squash and merge is preferred for clean history.

## Reporting Issues

Use GitHub Issues for:

- Bug reports
- Feature requests
- Questions about usage
- Documentation improvements

For security vulnerabilities, please see [SECURITY.md](SECURITY.md).

---

Thank you for contributing!