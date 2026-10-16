FRONTEND_DIR := frontend
BACKEND_DIR := backend
BACKEND_PYTHON := $(BACKEND_DIR)/.venv/bin/python

.PHONY: install backend-install dev backend-dev test backend-test typecheck lint build

install:
	cd $(FRONTEND_DIR) && npm ci

backend-install:
	python3 -m venv $(BACKEND_DIR)/.venv
	$(BACKEND_DIR)/.venv/bin/pip install -r $(BACKEND_DIR)/requirements.lock

dev:
	cd $(FRONTEND_DIR) && npm run dev -- --host 0.0.0.0

backend-dev:
	$(BACKEND_PYTHON) -m uvicorn app.main:app --app-dir $(BACKEND_DIR) --reload --host 0.0.0.0 --port 8000

test:
	cd $(FRONTEND_DIR) && npm test
	$(BACKEND_PYTHON) -m pytest $(BACKEND_DIR)/tests

backend-test:
	$(BACKEND_PYTHON) -m pytest $(BACKEND_DIR)/tests

typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

lint:
	cd $(FRONTEND_DIR) && npm run lint

build:
	cd $(FRONTEND_DIR) && npm run build
