.PHONY: setup format test compatibility check build

setup: ## Install project and development dependencies
	uv sync --all-groups

format: ## Format Python and fix lint violations
	uv run ruff format .
	uv run ruff check . --fix

test: ## Run the unittest suite
	uv run python -m unittest discover -s tests

compatibility: ## Test the minimum and current Sentry SDK contracts
	uv run --isolated --no-project --with "sentry-sdk==2.0.0" python -m unittest tests.test_sentry_contract
	uv run python -m unittest tests.test_sentry_contract

check: ## Check formatting, lint, and tests
	uv run ruff format --check .
	uv run ruff check .
	uv run python -m unittest discover -s tests

build: ## Build wheel and source distributions
	uv build
