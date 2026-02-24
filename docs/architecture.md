# Architecture & Design

## System Overview

This is a production-grade quantitative trading ML pipeline for cryptocurrency forecasting, deployed on AWS EKS with full MLOps capabilities.

**Key Features:**
- Real-time data ingestion from Binance API
- Advanced feature engineering with 30+ technical indicators
- XGBoost forecasting with MLflow experiment tracking
- Professional backtesting with transaction costs and risk controls
- Comprehensive risk metrics (Sharpe, Sortino, Max Drawdown, VaR, CVaR)
- Position sizing and risk management
- Model drift detection and monitoring
- FastAPI inference service with autoscaling
- Amazon Q integration for AI-powered development

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud (EKS)                            │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Kubernetes Cluster                         │  │
│  │                                                                │  │
│  │  ┌─────────────┐      ┌──────────────┐     ┌──────────────┐ │  │
│  │  │  Ingestion  │─────▶│   Feature    │────▶│   Training   │ │  │
│  │  │   Service   │      │  Engineering │     │   Service    │ │  │
│  │  │  (CronJob)  │      │   Service    │     │  (XGBoost)   │ │  │
│  │  └─────────────┘      └──────────────┘     └──────┬───────┘ │  │
│  │         │                                           │         │  │
│  │         │                                           ▼         │  │
│  │         │                                    ┌──────────────┐ │  │
│  │         │                                    │   MLflow     │ │  │
│  │         │                                    │   Tracking   │ │  │
│  │         │                                    └──────────────┘ │  │
│  │         │                                           │         │  │
│  │         ▼                                           │         │  │
│  │  ┌─────────────┐                                   │         │  │
│  │  │   S3/MinIO  │◀──────────────────────────────────┘         │  │
│  │  │ Data Lake   │                                             │  │
│  │  └─────────────┘                                             │  │
│  │         │                                                     │  │
│  │         │                                                     │  │
│  │         ▼                                                     │  │
│  │  ┌─────────────┐      ┌──────────────┐                      │  │
│  │  │  FastAPI    │◀─────│  Model       │                      │  │
│  │  │  Inference  │      │  Registry    │                      │  │
│  │  │  Service    │      │  (MLflow)    │                      │  │
│  │  └──────┬──────┘      └──────────────┘                      │  │
│  │         │                                                     │  │
│  │         │                                                     │  │
│  └─────────┼─────────────────────────────────────────────────────┘  │
│            │                                                         │
│            ▼                                                         │
│  ┌─────────────────┐                                                │
│  │  Load Balancer  │                                                │
│  │   (ALB/NLB)     │                                                │
│  └─────────────────┘                                                │
│            │                                                         │
└────────────┼─────────────────────────────────────────────────────────┘
             │
             ▼
      ┌─────────────┐
      │   Users /   │
      │  Traders    │
      └─────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      Monitoring & Observability                      │
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │  Prometheus  │─────▶│   Grafana    │      │  CloudWatch  │      │
│  │   Metrics    │      │  Dashboards  │      │     Logs     │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
└─────────────────────────────────────────────────────────────────────┘

External Data Source:
┌─────────────┐
│  Binance    │──────▶ Ingestion Service
│     API     │
└─────────────┘
```

## Component Details

### 1. Data Ingestion Service
- **Purpose**: Fetch OHLCV data from Binance API
- **Schedule**: CronJob running every 1 hour
- **Features**:
  - Rate limit handling
  - Retry logic with exponential backoff
  - Data validation
  - Stores raw data to S3/MinIO

### 2. Feature Engineering Service
- **Purpose**: Transform raw data into ML-ready features
- **Features**:
  - Technical indicators (RSI, MACD, Bollinger Bands, ATR)
  - Lag features (1h, 4h, 24h)
  - Rolling statistics (mean, std, min, max)
  - Time-based features (hour, day of week)
  - No data leakage validation

### 3. Training Service
- **Purpose**: Train XGBoost models with MLflow tracking
- **Features**:
  - Hyperparameter tuning
  - Cross-validation
  - Model versioning
  - Automatic model registration
  - Performance metrics logging

### 4. MLflow Tracking Server
- **Purpose**: Experiment tracking and model registry
- **Storage**:
  - Artifacts: S3/MinIO
  - Metadata: PostgreSQL
- **Features**:
  - Model versioning
  - A/B testing support
  - Model promotion workflow

### 5. FastAPI Inference Service
- **Purpose**: Real-time predictions
- **Features**:
  - Model caching
  - Request validation
  - Health checks
  - Prometheus metrics
  - Horizontal autoscaling (HPA)

### 6. Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **CloudWatch**: Logs aggregation
- **Alerts**: Model drift, API latency, error rates

## AWS Infrastructure

### EKS Cluster
- **Node Groups**: 
  - General: t3.medium (2-5 nodes)
  - ML Training: c5.2xlarge (0-3 nodes, spot instances)
- **Networking**: VPC with public/private subnets
- **Security**: IRSA for pod-level IAM permissions

### Storage
- **S3 Buckets**:
  - Raw data
  - Processed features
  - MLflow artifacts
  - Model registry
- **RDS PostgreSQL**: MLflow metadata store

### Compute
- **ECR**: Docker image registry
- **EKS**: Kubernetes orchestration
- **Lambda**: Optional for event-driven tasks

### Networking
- **ALB**: Application Load Balancer for API
- **Route53**: DNS management
- **VPC**: Isolated network

## Data Flow

1. **Ingestion**: Binance API → Ingestion Service → S3 (raw data)
2. **Features**: S3 (raw) → Feature Engineering → S3 (features)
3. **Training**: S3 (features) → Training Service → MLflow → Model Registry
4. **Inference**: API Request → FastAPI → Model Registry → Prediction
5. **Monitoring**: All services → Prometheus → Grafana

## Deployment Strategy

- **Rolling Updates**: Zero-downtime deployments
- **Autoscaling**: HPA based on CPU/memory and custom metrics
- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: Defined for all pods

## Security

- **Secrets**: AWS Secrets Manager + Kubernetes Secrets
- **IAM**: IRSA for fine-grained permissions
- **Network**: Private subnets for sensitive services
- **API**: Authentication via API keys

## Scalability

- **Horizontal**: HPA for API service (2-10 replicas)
- **Vertical**: Node autoscaling for training workloads
- **Data**: Partitioned by date in S3
- **Caching**: Model caching in API service

## Cost Optimization

- **Spot Instances**: For training workloads
- **S3 Lifecycle**: Archive old data to Glacier
- **Right-sizing**: Appropriate instance types
- **Autoscaling**: Scale down during low traffic
