# Local Development Guide

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Make
- Git

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/SrinathMLOps/QuantTradingMLPipeline.git
cd QuantTradingMLPipeline
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
make install
```

This will:
- Install Python packages from requirements.txt
- Set up pre-commit hooks for code quality

### 4. Configure Environment Variables

Create a `.env` file:

```bash
# Binance API
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_ENDPOINT_URL=http://localhost:9000

# AWS (for local MinIO)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# Database
DATABASE_URL=postgresql://mlflow:mlflow@localhost:5432/mlflow
```

### 5. Start Local Services with Docker Compose

```bash
docker-compose up -d
```

This starts:
- MLflow tracking server (port 5000)
- MinIO (S3-compatible storage, port 9000)
- PostgreSQL (port 5432)
- Prometheus (port 9090)
- Grafana (port 3000)

## Running the Pipeline

### Full Pipeline

```bash
# Run complete pipeline
python src/main.py
```

### Individual Components

```bash
# Data ingestion only
python src/ingestion/fetch_data.py

# Feature engineering only
python src/features/engineer_features.py

# Training only
python src/training/train_model.py

# Start API server
uvicorn src.api.main:app --reload --port 8000
```

## Testing

### Run All Tests

```bash
make test
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage report
pytest tests/ --cov=src --cov-report=html
```

## Code Quality

### Linting and Formatting

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:
- Black (formatting)
- Flake8 (linting)
- Trailing whitespace removal
- YAML validation

## Accessing Services

### MLflow UI
```bash
# Open browser to http://localhost:5000
make mlflow-ui
```

### MinIO Console
```bash
# Open browser to http://localhost:9001
# Login: minioadmin / minioadmin
```

### Grafana Dashboards
```bash
# Open browser to http://localhost:3000
# Login: admin / admin
```

### API Documentation
```bash
# Start API server
uvicorn src.api.main:app --reload

# Open browser to http://localhost:8000/docs
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code, add tests, update documentation.

### 3. Run Tests and Linting

```bash
make test
make lint
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Pre-commit hooks will run automatically.

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect MLflow Runs

```python
import mlflow

# List experiments
mlflow.search_experiments()

# Get run details
run = mlflow.get_run("run_id")
print(run.data.metrics)
print(run.data.params)
```

### Check Data Quality

```python
import pandas as pd

# Load raw data
df = pd.read_parquet("data/raw/BTCUSDT_1h.parquet")
print(df.info())
print(df.describe())
```

## Common Issues

### Issue: MLflow can't connect to database

**Solution**: Ensure PostgreSQL is running
```bash
docker-compose ps
docker-compose logs postgres
```

### Issue: Binance API rate limit

**Solution**: Add delays between requests or use cached data
```python
import time
time.sleep(1)  # Wait 1 second between requests
```

### Issue: Import errors

**Solution**: Ensure you're in the virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Project Structure

```
src/
├── ingestion/          # Data collection from Binance
│   ├── fetch_data.py
│   └── validators.py
├── features/           # Feature engineering
│   ├── engineer_features.py
│   └── indicators.py
├── training/           # Model training
│   ├── train_model.py
│   └── evaluate.py
├── api/                # FastAPI service
│   ├── main.py
│   ├── models.py
│   └── predict.py
└── utils/              # Shared utilities
    ├── config.py
    └── logger.py
```

## Next Steps

- Read [Architecture Documentation](architecture.md)
- Review [AWS Deployment Guide](aws-deployment.md)
- Check [Runbook](runbook.md) for troubleshooting
