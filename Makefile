FRONTEND_DIR := frontend

.PHONY: install dev test typecheck lint build

install:
	cd $(FRONTEND_DIR) && npm ci

dev:
	cd $(FRONTEND_DIR) && npm run dev -- --host 0.0.0.0

test:
	cd $(FRONTEND_DIR) && npm test

typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

lint:
	cd $(FRONTEND_DIR) && npm run lint

build:
	cd $(FRONTEND_DIR) && npm run build
