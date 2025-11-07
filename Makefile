## Makefile - convenience targets for development

.PHONY: deps-check test-org

# Run the service dependency checker for the image classifier
deps-check:
	@echo "Running dependency preflight for crank_image_classifier..."
	@python3 scripts/check-service-dependencies.py crank_image_classifier

# Validate test organization (tests/ vs scripts/ directories)
test-org:
	@./scripts/check-test-organization.sh
