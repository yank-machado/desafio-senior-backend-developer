.PHONY: help clean lint test coverage format install dev-install migrate run

help:  ## Mostra a lista de comandos
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

clean:  ## Remove arquivos temporários e caches
	rm -rf __pycache__/ build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:  ## Executa as verificações de qualidade de código
	isort .
	black .
	flake8 .
	mypy .

test:  ## Executa os testes
	pytest -xvs

coverage:  ## Executa testes com relatório de cobertura
	pytest --cov=. --cov-report=term --cov-report=html
	@echo "Abra htmlcov/index.html no navegador para ver o relatório detalhado"

format:  ## Formata o código automaticamente
	isort .
	black .

install:  ## Instala dependências para produção
	pip install -r requirements.txt

dev-install:  ## Instala dependências para desenvolvimento
	pip install -r requirements-dev.txt
	pre-commit install

dev:  ## Inicia o ambiente de desenvolvimento
	python start_dev.py

migrate:  ## Executa as migrações do banco de dados
	alembic upgrade head

run:  ## Executa a aplicação em modo de produção
	uvicorn main:app --host 0.0.0.0 --port 8000 