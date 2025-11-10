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

# ============================================================================
# 🐰 Wendy's Security Scanning Targets
# ============================================================================

# Scan base worker image for CVEs (informational)
security-scan:
	@echo "🐰 Wendy's Security Scan: Checking worker-base for CVEs..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image --severity CRITICAL,HIGH,MEDIUM \
		worker-base:latest
	@echo "✅ Security scan complete"

# Scan and FAIL on CRITICAL/HIGH CVEs (for CI/CD)
security-scan-ci:
	@echo "🐰 Wendy's CI Security Scan (fail on CRITICAL/HIGH)..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image --severity CRITICAL,HIGH --exit-code 1 \
		worker-base:latest
	@echo "✅ No CRITICAL/HIGH vulnerabilities found"

# Generate Software Bill of Materials (SBOM)
security-sbom:
	@echo "🐰 Generating SBOM for worker-base..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image --format cyclonedx \
		--output sbom-worker-base.json \
		worker-base:latest
	@echo "✅ SBOM generated: sbom-worker-base.json"

# Scan all worker images
security-scan-all:
	@echo "🐰 Scanning all worker images..."
	@for worker in streaming doc_converter email_parser image_classifier; do \
		echo ""; \
		echo "Scanning crank-$$worker..."; \
		docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
			aquasec/trivy image --severity CRITICAL,HIGH \
			crank-$$worker:latest 2>/dev/null || echo "⚠️  Image not found: crank-$$worker"; \
	done
	@echo "✅ All scans complete"

# Scan Dockerfile for misconfigurations
security-scan-dockerfile:
	@echo "🐰 Scanning Dockerfile for security issues..."
	@docker run --rm -v $(PWD):/src \
		aquasec/trivy config /src/services/Dockerfile.worker-base
	@echo "✅ Dockerfile scan complete"

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
	@echo "🐰 Wendy's Security Targets:"
	@echo "  security-scan           - Scan worker-base for CVEs (informational)"
	@echo "  security-scan-ci        - Scan and FAIL on CRITICAL/HIGH (for CI/CD)"
	@echo "  security-sbom           - Generate Software Bill of Materials"
	@echo "  security-scan-all       - Scan all worker images"
	@echo "  security-scan-dockerfile - Check Dockerfile for misconfigurations"
	@echo ""
	@echo "Examples:"
	@echo "  make worker-install WORKER=streaming"
	@echo "  make worker-run WORKER=streaming"
	@echo "  make worker-build WORKER=doc_converter"
	@echo "  make security-scan-ci  # Run before releases"
