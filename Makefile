.PHONY: dev test down logs clean

dev:
	docker compose up --build

dev-detached:
	docker compose up --build -d

test:
	docker compose run --rm backend pytest tests/ -v --tb=short

test-cov:
	docker compose run --rm backend pytest tests/ --cov=. --cov-report=term-missing

down:
	docker compose down -v

logs:
	docker compose logs -f backend

clean:
	docker compose down -v --rmi local