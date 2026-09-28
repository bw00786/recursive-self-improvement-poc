.PHONY: setup backend frontend test bootstrap sandbox-image docker-up

setup:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

backend:
	uvicorn backend.app.main:app --reload --port 8100

frontend:
	cd frontend && npm run dev

bootstrap:
	python scripts/bootstrap.py

test:
	cd backend && pytest -q

sandbox-image:
	docker build -t rail-sandbox:latest sandbox

docker-up:
	docker compose up -d
