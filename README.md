# QuantTradingMLPipeline

Production-grade cryptocurrency forecasting pipeline with MLOps best practices.

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed system design and data flow.

## Features

- Real-time crypto data ingestion from Binance API
- Feature engineering with technical indicators (RSI, MACD, Bollinger Bands)
- XGBoost-based forecasting with MLflow tracking
- FastAPI inference service
- Kubernetes deployment with autoscaling
- Prometheus monitoring and Grafana dashboards
- CI/CD with GitHub Actions

## Quick Start

### Local Development

```bash
# Install dependencies
make install

# Run pipeline locally
make run-local

# View MLflow UI
make mlflow-ui
```

### Deploy to AWS EKS

```bash
# Configure AWS credentials
aws configure

# Deploy infrastructure
cd infra/terraform
terraform init
terraform apply

# Deploy application
make deploy-k8s
```

## Project Structure

```
├── src/                    # Source code
│   ├── ingestion/         # Data collection
│   ├── features/          # Feature engineering
│   ├── training/          # Model training
│   └── api/               # FastAPI service
├── infra/                 # Infrastructure as code
│   ├── terraform/         # AWS EKS setup
│   └── k8s/              # Kubernetes manifests
├── docs/                  # Documentation
├── tests/                 # Unit and integration tests
├── monitoring/            # Observability configs
└── .github/workflows/     # CI/CD pipelines
```

## Documentation

- [Architecture & Design](docs/architecture.md)
- [Local Development Guide](docs/local-development.md)
- [AWS Deployment Guide](docs/aws-deployment.md)
- [Runbook & Troubleshooting](docs/runbook.md)

## Monitoring

- Prometheus metrics at `/metrics`
- Grafana dashboards in `monitoring/dashboards/`
- MLflow tracking UI for experiment management

## License

MIT
