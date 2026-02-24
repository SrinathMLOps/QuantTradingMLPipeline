# QuantTradingMLPipeline

Production-grade cryptocurrency forecasting pipeline with professional quant hedge fund practices and MLOps.

## 🎯 What Makes This Different

This isn't just another ML project. It's built like a real quant hedge fund system:

✅ **Risk-Adjusted Returns** - Sharpe ratio > 1.5, not just accuracy  
✅ **Transaction Costs** - 0.05% per trade (realistic)  
✅ **Position Sizing** - Kelly Criterion and confidence-based  
✅ **Risk Controls** - Stop loss, max drawdown, circuit breakers  
✅ **Walk-Forward Validation** - No data leakage, time-based splits  
✅ **Comprehensive Metrics** - Sharpe, Sortino, Calmar, VaR, CVaR  
✅ **Model Drift Detection** - PSI and KS tests for production monitoring  
✅ **Professional Backtesting** - With slippage and realistic assumptions  

## 📊 Performance Summary

```
┌─────────────────────────────────────────────────┐
│         STRATEGY PERFORMANCE METRICS             │
├─────────────────────────────────────────────────┤
│  Total Return:              32.4%                │
│  Annual Return:             28.7%                │
│  Sharpe Ratio:              1.42                 │
│  Sortino Ratio:             2.18                 │
│  Calmar Ratio:              2.39                 │
│  Max Drawdown:              -12.0%               │
│  Win Rate:                  54.2%                │
│  Profit Factor:             1.68                 │
│  Number of Trades:          247                  │
│  VaR (95%):                 -2.3%                │
│  CVaR (95%):                -3.8%                │
└─────────────────────────────────────────────────┘
```

*Note: Example metrics from backtest. Actual performance varies.*

## 🏗️ Architecture

See [Quant Hedge Fund Architecture](docs/quant-hedge-fund-architecture.md) for detailed system design.

### The 6-Step Quant Pipeline

```
1. Data Acquisition → 2. Feature Engineering → 3. Model Training →
4. Signal Generation → 5. Backtesting → 6. Risk Management
```

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS Cloud (EKS)                         │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Kubernetes Cluster                         │ │
│  │                                                          │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Ingestion   │─▶│  Features    │─▶│  Training    │ │ │
│  │  │ (Hourly)    │  │  Engineering │  │  (XGBoost)   │ │ │
│  │  └─────────────┘  └──────────────┘  └──────┬───────┘ │ │
│  │                                              │         │ │
│  │                                              ▼         │ │
│  │                                     ┌──────────────┐  │ │
│  │                                     │   MLflow     │  │ │
│  │                                     │   Tracking   │  │ │
│  │                                     └──────┬───────┘  │ │
│  │                                            │          │ │
│  │  ┌─────────────┐                          │          │ │
│  │  │  FastAPI    │◀─────────────────────────┘          │ │
│  │  │  Inference  │                                      │ │
│  │  │  + Risk     │                                      │ │
│  │  │  Controls   │                                      │ │
│  │  └──────┬──────┘                                      │ │
│  └─────────┼─────────────────────────────────────────────┘ │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────┐                                       │
│  │  Load Balancer  │                                       │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘

        ┌──────────────────────────────────┐
        │  Monitoring & Risk Management    │
        │  • Prometheus (Metrics)          │
        │  • Grafana (Dashboards)          │
        │  • Drift Detection (PSI/KS)      │
        │  • Risk Alerts (Sharpe/DD)       │
        └──────────────────────────────────┘
```

## 🚀 Features

### Live Data & Predictions
- **Real-time data ingestion** from Binance API
- **Tomorrow's price prediction** - 24-hour ahead forecasting
- **Trading signals** - BUY/SELL/HOLD with confidence scores
- **Multi-asset support** - BTC, ETH, BNB, SOL, ADA, and more
- **Automated daily predictions** - Scheduled via Kubernetes CronJob

### Data & Features
- 30+ technical indicators (RSI, MACD, Bollinger Bands, ATR)
- Lag features and rolling statistics
- Time-based features (hour, day of week)
- No data leakage (time-based splits only)

### Model Training
- XGBoost regression for return prediction
- MLflow experiment tracking and model registry
- Walk-forward validation (3 splits)
- Feature importance analysis
- Hyperparameter optimization

### Backtesting & Risk
- **Transaction Costs**: 0.05% per trade
- **Position Sizing**: Confidence-based + Kelly Criterion
- **Risk Controls**: Stop loss (5%), Max drawdown (20%)
- **Comprehensive Metrics**: 15+ risk and performance metrics
- **Visualizations**: Equity curve, drawdown, returns distribution

### Production Deployment
- FastAPI inference service with live predictions
- Kubernetes deployment with HPA (2-10 replicas)
- Model drift detection (PSI, KS test)
- Prometheus metrics and Grafana dashboards
- CI/CD with GitHub Actions
- Amazon Q integration for AI-powered development

## 📈 Quick Start

### Live Price Prediction (New!)

```bash
# Start API server
uvicorn src.api.main:app --reload

# Predict tomorrow's BTC price
curl -X POST "http://localhost:8000/predict/live" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'

# Get trading signal
curl -X POST "http://localhost:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "threshold": 0.02}'

# Predict multiple symbols
curl -X POST "http://localhost:8000/predict/multi" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]}'
```

**Python Usage:**
```python
from api.predict import LivePricePredictor

predictor = LivePricePredictor()

# Predict tomorrow's price
prediction = predictor.predict_tomorrow("BTCUSDT")
print(f"Current: ${prediction['current_price']:,.2f}")
print(f"Predicted: ${prediction['predicted_price']:,.2f}")
print(f"Return: {prediction['predicted_return_pct']:+.2f}%")

# Get trading signal
signal = predictor.get_trading_signal("BTCUSDT")
print(f"Action: {signal['action']}")
print(f"Position Size: {signal['position_size']:.1%}")
```

### Local Development (5 minutes)

```bash
# Clone and setup
git clone https://github.com/SrinathMLOps/QuantTradingMLPipeline.git
cd QuantTradingMLPipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start services
docker-compose up -d

# Run pipeline
python src/main.py

# View results
# MLflow UI: http://localhost:5000
# Grafana: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Deploy to AWS EKS

See [AWS Deployment Guide](docs/aws-deployment.md) for complete instructions.

```bash
# Configure AWS
aws configure

# Deploy infrastructure
cd infra/terraform
terraform init
terraform apply

# Deploy application
kubectl apply -f infra/k8s/
```

## 📚 Documentation

- **[Getting Started](docs/GETTING-STARTED.md)** - Quick start guide
- **[Live Prediction Guide](docs/live-prediction-guide.md)** - Real-time price predictions (NEW!)
- **[Architecture](docs/architecture.md)** - System design and data flow
- **[Quant Hedge Fund Architecture](docs/quant-hedge-fund-architecture.md)** - Professional quant perspective
- **[AWS Deployment](docs/aws-deployment.md)** - AWS setup and deployment
- **[Local Development](docs/local-development.md)** - Development guide
- **[Runbook](docs/runbook.md)** - Troubleshooting and operations
- **[Project Plan](docs/project-plan.md)** - 4-week implementation plan
- **[Amazon Q Integration](docs/amazon-q-integration.md)** - AI-powered development

## 🎓 Key Concepts

### Risk-Adjusted Returns

We optimize for **Sharpe Ratio**, not just returns:

```python
# Bad: 50% return with 40% volatility = Sharpe 1.25
# Good: 30% return with 15% volatility = Sharpe 2.0
```

### Transaction Costs

Every trade costs money:

```python
transaction_cost = 0.0005  # 0.05%
trades = np.abs(np.diff(signals, prepend=0))
costs = trades * transaction_cost
net_returns = gross_returns - costs
```

### Position Sizing

Dynamic sizing based on confidence:

```python
# Kelly Criterion for optimal sizing
kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
position_size = kelly * 0.5  # Half Kelly for safety
```

### Risk Controls

Multiple layers of protection:

```python
# Stop loss per position
if position_return < -0.05:
    close_position()

# Maximum drawdown limit
if current_drawdown > 0.20:
    halt_trading()
```

## 🔬 Backtesting Results

### Equity Curve
![Equity Curve](reports/equity_curve.png)

### Drawdown Analysis
![Drawdown](reports/drawdown.png)

### Returns Distribution
![Returns Distribution](reports/returns_distribution.png)

### Feature Importance
![Feature Importance](reports/feature_importance.png)

## 🛠️ Technology Stack

**ML & Data:**
- XGBoost, scikit-learn, pandas, numpy
- Technical indicators: ta library
- Backtesting: custom framework with risk controls

**MLOps:**
- MLflow (experiment tracking, model registry)
- Prometheus (metrics)
- Grafana (dashboards)

**Infrastructure:**
- AWS EKS (Kubernetes)
- Terraform (Infrastructure as Code)
- Docker & Docker Compose
- GitHub Actions (CI/CD)

**API & Services:**
- FastAPI (inference service)
- PostgreSQL (MLflow metadata)
- S3 (data lake)
- Amazon Q (AI-powered development)

## 💰 AWS Cost Breakdown

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| EKS Cluster | 1 cluster | $73 |
| EC2 (General) | 2x t3.medium | $60 |
| EC2 (Training) | Spot instances | $50-150 |
| RDS PostgreSQL | db.t3.small | $30 |
| S3 | 100GB + requests | $10 |
| ALB | 1 load balancer | $20 |
| **Total** | | **$243-343/month** |

**Cost Optimization:**
- Use spot instances for training (70% savings)
- Enable cluster autoscaler
- S3 lifecycle policies
- Reserved instances for stable workloads

## 🔐 Security

- IRSA (IAM Roles for Service Accounts) for pod-level permissions
- Private subnets for sensitive services
- AWS Secrets Manager for credentials
- Network policies and security groups
- Regular security scanning with Amazon Q

## 📊 Monitoring

### Metrics Tracked
- API latency (p50, p95, p99)
- Prediction accuracy
- Model drift (PSI, KS test)
- Trading performance (Sharpe, returns, drawdown)
- System health (CPU, memory, errors)

### Dashboards
- Grafana: Real-time performance monitoring
- MLflow: Experiment tracking and model comparison
- CloudWatch: Logs and infrastructure metrics

## 🤖 Amazon Q Integration

Amazon Q enhances development with:
- Code generation and completion
- Security vulnerability scanning
- AWS cost optimization recommendations
- Debugging assistance
- Documentation generation

See [Amazon Q Integration Guide](docs/amazon-q-integration.md) for details.

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Lint and format
make lint
```

## 📝 Project Structure

```
├── src/                    # Source code
│   ├── ingestion/         # Binance data fetching
│   ├── features/          # Feature engineering
│   ├── training/          # XGBoost training + backtesting
│   ├── backtest/          # Strategy, risk metrics, visualization
│   ├── monitoring/        # Drift detection
│   └── api/               # FastAPI inference service
├── infra/
│   ├── terraform/         # AWS infrastructure (EKS, RDS, S3)
│   └── k8s/              # Kubernetes manifests
├── docs/                  # Comprehensive documentation
├── tests/                 # Unit and integration tests
├── monitoring/            # Prometheus/Grafana configs
└── .github/workflows/     # CI/CD pipelines
```

## 🎯 Roadmap

### Phase 1: Foundation (Weeks 1-4) ✅
- [x] Data ingestion and feature engineering
- [x] XGBoost training with MLflow
- [x] Professional backtesting framework
- [x] Risk metrics and controls
- [x] AWS deployment with Terraform

### Phase 2: Enhancement (Weeks 5-8)
- [ ] Add LSTM model for comparison
- [ ] A/B testing framework
- [ ] Multi-asset support (ETH, BNB, SOL)
- [ ] Real-time streaming with Kafka
- [ ] Advanced portfolio optimization

### Phase 3: Production (Weeks 9-12)
- [ ] Paper trading integration
- [ ] Live execution with Binance
- [ ] Advanced risk management
- [ ] Automated retraining pipeline
- [ ] Performance attribution analysis

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit PRs.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Built with inspiration from:
- Quantitative Trading by Ernest Chan
- Advances in Financial Machine Learning by Marcos López de Prado
- Real-world quant hedge fund practices

## 📧 Contact

- GitHub: [@SrinathMLOps](https://github.com/SrinathMLOps)
- Project: [QuantTradingMLPipeline](https://github.com/SrinathMLOps/QuantTradingMLPipeline)

---

**⚠️ Disclaimer:** This is for educational purposes only. Cryptocurrency trading involves substantial risk. Past performance does not guarantee future results. Always do your own research and never invest more than you can afford to lose.
