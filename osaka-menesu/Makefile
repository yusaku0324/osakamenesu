SHELL := /bin/bash

up:
	docker compose up -d --build db meili

api:
	docker compose up -d --build api && docker compose logs -f api

web:
	docker compose up -d --build web && docker compose logs -f web

dev:
	cp -n .env.example .env || true
	docker compose up -d --build
	docker compose logs -f api web

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

reset-db:
	docker compose down -v db && docker compose up -d db

seed:
	docker compose exec api python seed_dev.py
