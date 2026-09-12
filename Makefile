.PHONY: setup format test check build

setup: ## Install project and development dependencies
	uv sync --all-groups

format: ## Format Python and fix lint violations
	uv run ruff format .
	uv run ruff check . --fix

test: ## Run the unittest suite
	uv run python -m unittest discover -s tests

check: ## Check formatting, lint, and tests
	uv run ruff format --check .
	uv run ruff check .
	uv run python -m unittest discover -s tests

build: ## Build wheel and source distributions
	uv build
