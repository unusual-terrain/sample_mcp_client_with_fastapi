# Variables

PACKAGE_MANAGER = uv
APP_DIR = app

# Install dependencies
install:
	$(PACKAGE_MANAGER) sync

# Run app in dev mode
run-dev:
	$(PACKAGE_MANAGER) run uvicorn main:${APP_DIR} --reload --host 0.0.0.0 --port 8001

