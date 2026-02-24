.PHONY: install test lint run-local mlflow-ui docker-build deploy-k8s clean

install:
	pip install -r requirements.txt
	pre-commit install

test:
	pytest tests/ -v --cov=src

lint:
	black src/ tests/
	flake8 src/ tests/
	mypy src/

run-local:
	python src/main.py

mlflow-ui:
	mlflow ui --host 0.0.0.0 --port 5000

docker-build:
	docker build -t quant-trading-ml:latest .

docker-compose-up:
	docker-compose up -d

deploy-k8s:
	kubectl apply -f infra/k8s/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
