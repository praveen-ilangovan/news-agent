##################
###   INSTALL  ###
.PHONY: install
install: ## Install the poetry environment and pre-commit hooks
	@echo "🚀 Creating virtual environment using poetry"
	@poetry install
	@poetry run pre-commit install

##################
##  PRECOMMIT  ###
.PHONY: check
check: ## Run code quality tools (lock check, ruff, mypy).
	@echo "🚀 Checking Poetry lock file consistency: poetry check --lock"
	@poetry check --lock
	@echo "🚀 Running pre-commit: ruff lint, fmt and mypy"
	@poetry run pre-commit run --all-files

##################
###### TEST ######
.PHONY: unittest
unittest: ## Run unit tests
	@echo "🚀 Running unit tests"
	@poetry run pytest tests/unit

.PHONY: test-integration
test-integration: ## Run integration tests (hit the network / live APIs)
	@echo "🚀 Running integration tests"
	@poetry run pytest tests/integration -v

##################
#####  RUN   #####
.PHONY: run
run: ## Run the digest pipeline once (honours config.yaml)
	@poetry run news-agent run

.PHONY: fetch
fetch: ## Fetch all sources and print them (no ranking yet)
	@poetry run news-agent fetch

.PHONY: rank
rank: ## Fetch + rank + print the top-N per category
	@poetry run news-agent rank

.PHONY: summarize
summarize: ## Fetch + rank + LLM-summarize the top-N per category
	@poetry run news-agent summarize

##################
#####  HELP  #####
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
