.PHONY: install lint format test test-cov validate compose-up compose-down smoke demo clean

install:
	python -m pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	pytest -q

test-cov:
	pytest --cov --cov-report=term-missing --cov-report=xml

validate:
	python scripts/validate_repository.py

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down --remove-orphans

smoke:
	python -m scripts.smoke_test

demo:
	python -m scripts.simulate_incident

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov coverage.xml .coverage
