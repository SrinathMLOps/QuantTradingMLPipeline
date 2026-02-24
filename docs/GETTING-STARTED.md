# Getting Started

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone https://github.com/SrinathMLOps/QuantTradingMLPipeline.git
cd QuantTradingMLPipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Local Services

```bash
docker-compose up -d
```

Wait 30 seconds for services to start.

### 3. Run Pipeline

```bash
python src/main.py
```

### 4. View Results

- MLflow UI: http://localhost:5000
- Grafana: http://localhost:3000 (admin/admin)
- MinIO: http://localhost:9001 (minioadmin/minioadmin)

## What Just Happened?

1. **Data Ingestion**: Fetched 90 days of Bitcoin OHLCV data from Binance
2. **Feature Engineering**: Created 30+ technical indicators and features
3. **Model Training**: Trained XGBoost model with MLflow tracking
4. **Logging**: All experiments logged to MLflow with metrics and artifacts

## Next Steps

### Local Development
- Read [Local Development Guide](local-development.md)
- Modify features in `src/features/engineer_features.py`
- Tune hyperparameters in `src/training/train_model.py`
- Run tests: `make test`

### Deploy to AWS
- Read [AWS Deployment Guide](aws-deployment.md)
- Configure AWS credentials
- Run Terraform: `cd infra/terraform && terraform apply`
- Deploy app: `make deploy-k8s`

### Start API Server
```bash
uvicorn src.api.main:app --reload
# Visit http://localhost:8000/docs
```

## Troubleshooting

**Issue: Docker Compose fails**
```bash
docker-compose down -v
docker-compose up -d
```

**Issue: Binance API rate limit**
- Get free API key from Binance
- Add to `.env` file

**Issue: MLflow can't connect**
```bash
docker-compose logs mlflow
docker-compose restart mlflow
```

## Project Structure

```
├── src/                    # Source code
│   ├── ingestion/         # Binance data fetching
│   ├── features/          # Feature engineering
│   ├── training/          # XGBoost training
│   └── api/               # FastAPI service
├── infra/                 # Infrastructure
│   ├── terraform/         # AWS setup
│   └── k8s/              # Kubernetes manifests
├── docs/                  # Documentation
├── tests/                 # Tests
└── monitoring/            # Prometheus/Grafana
```

## Key Commands

```bash
make install        # Install dependencies
make test          # Run tests
make lint          # Check code quality
make run-local     # Run full pipeline
make mlflow-ui     # Open MLflow UI
make docker-build  # Build Docker images
make deploy-k8s    # Deploy to Kubernetes
```

## Learning Resources

- [Architecture Overview](architecture.md)
- [Project Plan](project-plan.md)
- [Runbook](runbook.md)
- [ADR: Model Choice](decisions/ADR-001-model-choice.md)

## Support

- Check [Runbook](runbook.md) for common issues
- Review [GitHub Issues](https://github.com/SrinathMLOps/QuantTradingMLPipeline/issues)
- Read documentation in `docs/`
