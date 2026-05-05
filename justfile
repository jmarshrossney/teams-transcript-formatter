_:
  @just lint typecheck test

# Format and lint the package using ruff.
lint:
  ruff format
  ruff check --fix

# Run static type checker.
typecheck:
  pyright

# Run the test suite using pytest.
test:
  pytest
