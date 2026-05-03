_:
  @just lint typecheck test

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check

# Run static type checker.
typecheck:
  pyright

# Run the test suite using pytest.
test:
  pytest
