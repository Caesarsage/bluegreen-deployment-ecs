
.PHONY: help setup test clean deploy

help:
	@echo "Available commands:"
	@echo "  make setup       - Set up local development environment"
	@echo "  make test        - Run tests"
	@echo "  make start       - Start local blue-green environment"
	@echo "  make migrate-expand - Run expand migration"
	@echo "  make migrate-contract - Run contract migration"
	@echo "  make monitor     - Run synthetic monitoring"
	@echo "  make clean       - Clean up Docker containers"

setup:
	pip install -r app/requirements.txt
	pip install pytest requests
	chmod +x scripts/*.sh

start:
	docker-compose -f docker/docker-compose.yml up -d
	@echo "\n✅ Services started!"
	@echo "Blue environment: http://localhost:8080"
	@echo "Green environment: http://localhost:8081"
	@echo "Database: localhost:5432"


clean:
	docker-compose -f docker/docker-compose.yml down -v
	@echo "\n🧹 Cleaned up Docker containers and volumes."
	@echo "You can start fresh with 'make start'."

migrate-expand:
	docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d ecommerce -f /docker-entrypoint-initdb.d/../migrations/001_expand_address.sql

migrate-contract:
	@echo "⚠️  WARNING: This will remove the old 'address' column!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $REPLY =~ ^[Yy]$ ]]; then \
		docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d ecommerce -f /docker-entrypoint-initdb.d/../migrations/002_contract_address.sql; \
	fi

test:
	pytest tests/ -v

monitor:
	python tests/synthetic_monitor.py

logs-blue:
	docker-compose -f docker/docker-compose.yml logs -f app-blue

logs-green:
	docker-compose -f docker/docker-compose.yml logs -f app-green

clean:
	docker-compose -f docker/docker-compose.yml down -v

rebuild:
	docker-compose -f docker/docker-compose.yml up -d --build
