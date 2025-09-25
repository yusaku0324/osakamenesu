SHELL := /bin/bash

COMPOSE := docker compose -f docker-compose.yml
ENV_FILE := .env

.PHONY: osakamenesu-env osakamenesu-up osakamenesu-api osakamenesu-web \
	osakamenesu-dev osakamenesu-down osakamenesu-logs osakamenesu-ps \
	osakamenesu-reset-db osakamenesu-seed

osakamenesu-env:
	cp -n $(ENV_FILE).example $(ENV_FILE) || true

osakamenesu-up: osakamenesu-env
	$(COMPOSE) up -d --build osakamenesu-db osakamenesu-meili

osakamenesu-api: osakamenesu-env
	$(COMPOSE) up -d --build osakamenesu-api
	$(COMPOSE) logs -f osakamenesu-api

osakamenesu-web: osakamenesu-env
	$(COMPOSE) up -d --build osakamenesu-web
	$(COMPOSE) logs -f osakamenesu-web

osakamenesu-dev: osakamenesu-env
	$(COMPOSE) up -d --build
	$(COMPOSE) logs -f osakamenesu-api osakamenesu-web

osakamenesu-down:
	$(COMPOSE) down

osakamenesu-logs:
	$(COMPOSE) logs -f

osakamenesu-ps:
	$(COMPOSE) ps

osakamenesu-reset-db:
	$(COMPOSE) down -v
	$(COMPOSE) up -d osakamenesu-db

osakamenesu-seed:
	$(COMPOSE) exec osakamenesu-api python seed_dev.py
