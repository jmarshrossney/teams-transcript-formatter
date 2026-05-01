_:
  @just --list

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check

# Run the test suite using pytest.
test:
  pytest

# Run static type checker.
typecheck:
  pyright
