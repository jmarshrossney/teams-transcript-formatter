# Contributing

Thank you for your interest in contributing to teams-transcript-formatter!

## Setting up your development environment

See the [README](README.md#from-source) for instructions on cloning the repository and installing dependencies with `uv sync`.

## Pre-commit hooks

This project uses [pre-commit](https://pre-commit.com/) to run formatting, linting, type-checking, and tests before every commit via the `just` command runner.

### Install pre-commit

```sh
pip install pre-commit
```

or

```sh
uv tool install pre-commit
```

### Enable the hooks

Run this once after cloning the repository:

```sh
pre-commit install
```

This installs a git hook that runs `just` (which in turn runs `ruff format`, `ruff check`, `pyright`, and `pytest`) before each commit.
If any check fails, the commit will be blocked until the issues are resolved.

You can also run the checks manually at any time:

```sh
pre-commit run --all-files
```

or simply run the `just` command directly:

```sh
just
```

## No CI workflow

This project does not have a continuous integration (CI) workflow. The pre-commit hooks are considered sufficient to catch issues locally before code is pushed. Please make sure all hooks pass before opening a pull request.

## Opening a pull request

1. Fork the repository and create a branch for your changes.
2. Make your changes and commit them (pre-commit hooks will run automatically).
3. Push your branch to your fork.
4. Open a pull request against the `main` branch of this repository.
