.PHONY: install setup demo test lint run clean seed stage help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install --upgrade pip
	pip install -r requirements.txt

setup: install seed stage ## Full setup: install deps, seed database, upload semantic model

seed: ## Create Snowflake tables and populate with mock data
	python3 scripts/setup_db.py

stage: ## Upload semantic model to Snowflake stage for Cortex Analyst
	@echo "Creating stage and uploading semantic model..."
	python3 -c "\
import snowflake.connector; \
import os; \
from dotenv import load_dotenv; \
load_dotenv(); \
conn = snowflake.connector.connect( \
    account=os.getenv('SNOWFLAKE_ACCOUNT'), \
    user=os.getenv('SNOWFLAKE_USER'), \
    password=os.getenv('SNOWFLAKE_PASSWORD'), \
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'), \
    database=os.getenv('SNOWFLAKE_DATABASE'), \
    schema=os.getenv('SNOWFLAKE_SCHEMA'), \
    role=os.getenv('SNOWFLAKE_ROLE')); \
cur = conn.cursor(); \
cur.execute(\"CREATE STAGE IF NOT EXISTS SEMANTIC_MODELS DIRECTORY = (ENABLE = TRUE)\"); \
cur.execute(\"PUT file://semantic_model/paas_command_center.yaml @SEMANTIC_MODELS AUTO_COMPRESS=FALSE OVERWRITE=TRUE\"); \
print('Semantic model uploaded to @SEMANTIC_MODELS'); \
cur.close(); conn.close()"

demo: ## Run the interactive demo (no credentials needed)
	python3 demo.py --mock

demo-live: ## Run the demo with live Snowflake connection
	python3 demo.py

run: ## Start the FastAPI server locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run the test suite
	pytest tests/ -v

lint: ## Run flake8 linting
	flake8 app/ --max-complexity=10

clean: ## Remove cached files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
