.PHONY: setup docker-up docker-down db-init load-data load-all load-toronto load-toronto-only seed-data run test dbt-run dbt-test lint format ci deploy clean help logs run-detached etl-toronto

# Default target
.DEFAULT_GOAL := help

# Environment
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
DOCKER_COMPOSE := docker compose

# Architecture detection for Docker images
ARCH := $(shell uname -m)
ifeq ($(ARCH),aarch64)
    POSTGIS_IMAGE := imresamu/postgis:16-3.4
else ifeq ($(ARCH),arm64)
    POSTGIS_IMAGE := imresamu/postgis:16-3.4
else
    POSTGIS_IMAGE := postgis/postgis:16-3.4
endif
export POSTGIS_IMAGE

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================

setup: ## Install dependencies, create .env, init pre-commit
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install -e ".[dev,dbt]"
	@echo "$(GREEN)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Created .env from .env.example - please update values$(NC)"; fi
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)Setup complete!$(NC)"

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start PostgreSQL + PostGIS containers
	@echo "$(GREEN)Starting database containers...$(NC)"
	@echo "$(BLUE)Architecture: $(ARCH) -> Using image: $(POSTGIS_IMAGE)$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Waiting for database to be ready...$(NC)"
	@sleep 3
	@echo "$(GREEN)Database containers started!$(NC)"

docker-down: ## Stop containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) down

docker-logs: ## View container logs
	$(DOCKER_COMPOSE) logs -f

# =============================================================================
# Database
# =============================================================================

db-init: ## Initialize database schema
	@echo "$(GREEN)Initializing database schema...$(NC)"
	$(PYTHON) scripts/db/init_schema.py

db-reset: ## Drop and recreate database (DESTRUCTIVE)
	@echo "$(YELLOW)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d
	@sleep 3
	$(MAKE) db-init

# Domain-specific data loading
load-toronto: ## Load Toronto data from APIs
	@echo "$(GREEN)Loading Toronto neighbourhood data...$(NC)"
	$(PYTHON) scripts/data/load_toronto_data.py
	@echo "$(GREEN)Seeding Toronto development data...$(NC)"
	$(PYTHON) scripts/data/seed_amenity_data.py

load-toronto-only: ## Load Toronto data without running dbt or seeding
	@echo "$(GREEN)Loading Toronto data (skip dbt)...$(NC)"
	$(PYTHON) scripts/data/load_toronto_data.py --skip-dbt

# Aggregate data loading
load-data: load-toronto ## Load all project data (currently: Toronto)
	@echo "$(GREEN)All data loaded!$(NC)"

load-all: load-data ## Alias for load-data

seed-data: ## Seed sample development data (amenities, median_age)
	@echo "$(GREEN)Seeding development data...$(NC)"
	$(PYTHON) scripts/data/seed_amenity_data.py

# =============================================================================
# Testing
# =============================================================================

test: ## Run pytest
	@echo "$(GREEN)Running tests...$(NC)"
	pytest

test-cov: ## Run pytest with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	pytest --cov=portfolio_app --cov-report=html --cov-report=term

# =============================================================================
# dbt
# =============================================================================

dbt-run: ## Run dbt models
	@echo "$(GREEN)Running dbt models...$(NC)"
	@set -a && . ./.env && set +a && cd dbt && dbt run --profiles-dir .

dbt-test: ## Run dbt tests
	@echo "$(GREEN)Running dbt tests...$(NC)"
	@set -a && . ./.env && set +a && cd dbt && dbt test --profiles-dir .

dbt-docs: ## Generate dbt documentation
	@echo "$(GREEN)Generating dbt docs...$(NC)"
	@set -a && . ./.env && set +a && cd dbt && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run ruff linter
	@echo "$(GREEN)Running linter...$(NC)"
	ruff check .

format: ## Run ruff formatter
	@echo "$(GREEN)Formatting code...$(NC)"
	ruff format .
	ruff check --fix .

typecheck: ## Run mypy type checker
	@echo "$(GREEN)Running type checker...$(NC)"
	mypy dataflow

ci: ## Run all checks (lint, typecheck, test)
	@echo "$(GREEN)Running CI checks...$(NC)"
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	@echo "$(GREEN)All checks passed!$(NC)"

# =============================================================================
# Operations
# =============================================================================

logs: ## Follow docker compose logs (usage: make logs or make logs SERVICE=postgres)
	@./scripts/logs.sh $(SERVICE)

run-detached: ## Start containers and wait for health check
	@./scripts/run-detached.sh

etl-toronto: ## Run Toronto ETL pipeline (usage: make etl-toronto MODE=--full)
	@./scripts/etl/toronto.sh $(MODE)

# =============================================================================
# Deployment
# =============================================================================

deploy: ## Deploy to production
	@echo "$(YELLOW)Deployment not yet configured$(NC)"
	@echo "TODO: Add deployment script"

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"
