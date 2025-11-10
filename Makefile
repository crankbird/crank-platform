## Makefile - convenience targets for development

.PHONY: deps-check test-org worker-base worker-install worker-run

# ============================================================================
# Legacy Development Targets
# ============================================================================

# Run the service dependency checker for the image classifier
deps-check:
	@echo "Running dependency preflight for crank_image_classifier..."
	@python3 scripts/check-service-dependencies.py crank_image_classifier

# Validate test organization (tests/ vs scripts/ directories)
test-org:
	@./scripts/check-test-organization.sh

# ============================================================================
# Phase 2: Base Worker Image & Hybrid Deployment
# ============================================================================

# Build base worker image (shared by all workers)
worker-base:
	@echo "Building worker-base image..."
	docker build -f services/Dockerfile.worker-base -t worker-base:latest .
	@echo "✅ Base image built: worker-base:latest"

# Build specific worker from base
# Usage: make worker-build WORKER=streaming
worker-build: worker-base
	@if [ -z "$(WORKER)" ]; then \
		echo "❌ Error: WORKER not specified"; \
		echo "Usage: make worker-build WORKER=streaming"; \
		exit 1; \
	fi
	@echo "Building crank-$(WORKER) from base image..."
	docker build -f services/Dockerfile.crank-$(WORKER).new \
		-t crank-$(WORKER):latest .
	@echo "✅ Worker image built: crank-$(WORKER):latest"

# Install worker for native execution (macOS, non-containerized)
# Usage: make worker-install WORKER=streaming
worker-install:
	@if [ -z "$(WORKER)" ]; then \
		echo "❌ Error: WORKER not specified"; \
		echo "Usage: make worker-install WORKER=streaming"; \
		exit 1; \
	fi
	@echo "Installing crank-$(WORKER) for native execution..."
	@if [ ! -d ".venv-$(WORKER)" ]; then \
		python3 -m venv .venv-$(WORKER); \
		echo "✅ Created virtual environment: .venv-$(WORKER)"; \
	fi
	@.venv-$(WORKER)/bin/pip install --upgrade pip
	@.venv-$(WORKER)/bin/pip install -e src/
	@if [ -f "requirements-$(WORKER).txt" ]; then \
		.venv-$(WORKER)/bin/pip install -r requirements-$(WORKER).txt; \
	fi
	@echo "✅ Worker installed in .venv-$(WORKER)"
	@echo "Run with: make worker-run WORKER=$(WORKER)"

# Run worker natively (non-containerized)
# Usage: make worker-run WORKER=streaming
worker-run:
	@if [ -z "$(WORKER)" ]; then \
		echo "❌ Error: WORKER not specified"; \
		echo "Usage: make worker-run WORKER=streaming"; \
		exit 1; \
	fi
	@if [ ! -d ".venv-$(WORKER)" ]; then \
		echo "❌ Worker not installed. Run: make worker-install WORKER=$(WORKER)"; \
		exit 1; \
	fi
	@echo "Running crank-$(WORKER) natively..."
	@.venv-$(WORKER)/bin/python services/crank_$(WORKER).py

# Clean worker virtual environments
worker-clean:
	@echo "Cleaning worker virtual environments..."
	@rm -rf .venv-*
	@echo "✅ Cleaned all worker venvs"

# Help target
help:
	@echo "Crank Platform - Development Targets"
	@echo ""
	@echo "Legacy:"
	@echo "  deps-check        - Check image classifier dependencies"
	@echo "  test-org          - Validate test organization"
	@echo ""
	@echo "Phase 2 - Worker Deployment:"
	@echo "  worker-base       - Build base worker Docker image"
	@echo "  worker-build      - Build worker from base (WORKER=streaming)"
	@echo "  worker-install    - Install worker for native execution (WORKER=streaming)"
	@echo "  worker-run        - Run worker natively (WORKER=streaming)"
	@echo "  worker-clean      - Remove all worker virtual environments"
	@echo ""
	@echo "Examples:"
	@echo "  make worker-install WORKER=streaming"
	@echo "  make worker-run WORKER=streaming"
	@echo "  make worker-build WORKER=doc_converter"
