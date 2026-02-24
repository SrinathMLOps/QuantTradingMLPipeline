# AWS Deployment Guide

## Prerequisites

- AWS CLI configured with appropriate credentials
- kubectl installed
- terraform >= 1.5
- Docker installed
- eksctl (optional, for quick cluster setup)

## AWS Services Used

### Core Infrastructure
1. **EKS (Elastic Kubernetes Service)**: Container orchestration
2. **ECR (Elastic Container Registry)**: Docker image storage
3. **S3**: Data lake for raw data, features, and MLflow artifacts
4. **RDS PostgreSQL**: MLflow metadata store
5. **ALB (Application Load Balancer)**: API ingress
6. **VPC**: Network isolation
7. **IAM**: Security and permissions (IRSA)
8. **CloudWatch**: Logging and monitoring
9. **Secrets Manager**: Secure credential storage

### Optional Services
- **Lambda**: Event-driven processing
- **SQS**: Message queuing for async tasks
- **CloudFront**: CDN for API (if global)
- **Route53**: DNS management

## Step-by-Step Deployment

### 1. Set Up AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### 2. Create S3 Buckets

```bash
# Terraform state bucket (do this first)
aws s3 mb s3://quant-trading-terraform-state --region us-east-1

# Application buckets (or let Terraform create them)
aws s3 mb s3://quant-trading-raw-data
aws s3 mb s3://quant-trading-features
aws s3 mb s3://quant-trading-mlflow-artifacts
```

### 3. Deploy Infrastructure with Terraform

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply (creates EKS, RDS, VPC, IAM, etc.)
terraform apply

# Save outputs
terraform output -json > outputs.json
```

**What Terraform Creates:**
- VPC with public/private subnets across 3 AZs
- EKS cluster with managed node groups
- RDS PostgreSQL for MLflow
- S3 buckets with lifecycle policies
- IAM roles with IRSA for pods
- Security groups
- ECR repositories

### 4. Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig --name quant-trading-cluster --region us-east-1

# Verify connection
kubectl get nodes
```

### 5. Install Kubernetes Add-ons

```bash
# AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=quant-trading-cluster

# Metrics Server (for HPA)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Prometheus + Grafana (monitoring)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

### 6. Create Kubernetes Secrets

```bash
# Binance API credentials
kubectl create secret generic binance-api \
  --from-literal=api-key=YOUR_BINANCE_API_KEY \
  --from-literal=api-secret=YOUR_BINANCE_API_SECRET

# AWS credentials (if not using IRSA)
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY \
  --from-literal=secret-access-key=YOUR_SECRET_KEY

# MLflow database connection
kubectl create secret generic mlflow-db \
  --from-literal=connection-string=postgresql://user:pass@rds-endpoint:5432/mlflow
```

### 7. Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build images
docker build -t quant-trading-ingestion:latest -f docker/Dockerfile.ingestion .
docker build -t quant-trading-training:latest -f docker/Dockerfile.training .
docker build -t quant-trading-api:latest -f docker/Dockerfile.api .

# Tag images
docker tag quant-trading-ingestion:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-ingestion:latest
docker tag quant-trading-training:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-training:latest
docker tag quant-trading-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-api:latest

# Push images
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-ingestion:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-training:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-api:latest
```

### 8. Deploy Application to Kubernetes

```bash
# Deploy all services
kubectl apply -f infra/k8s/

# Check deployment status
kubectl get pods
kubectl get services
kubectl get ingress

# Get API endpoint
kubectl get ingress api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### 9. Verify Deployment

```bash
# Check API health
curl http://YOUR_ALB_ENDPOINT/health

# Check MLflow UI
kubectl port-forward svc/mlflow 5000:5000
# Visit http://localhost:5000

# Check Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# Visit http://localhost:3000 (admin/prom-operator)
```

## Architecture Decisions

### Why EKS?
- Managed Kubernetes reduces operational overhead
- Native AWS integration (IAM, ALB, CloudWatch)
- Autoscaling for variable workloads
- Easy CI/CD integration

### Why RDS for MLflow?
- Managed backups and high availability
- Better performance than SQLite
- Multi-AZ deployment for production

### Why S3 for Data Lake?
- Unlimited scalability
- Cost-effective storage
- Lifecycle policies for archival
- Native integration with ML tools

### Node Group Strategy
- **General Pool**: t3.medium for API and services (always on)
- **Training Pool**: c5.2xlarge spot instances (scale to zero when idle)
- **Cost Savings**: ~70% cheaper with spot for training

## Cost Estimation (Monthly)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| EKS Cluster | 1 cluster | $73 |
| EC2 (General) | 2x t3.medium | $60 |
| EC2 (Training) | Spot, on-demand | $50-200 |
| RDS PostgreSQL | db.t3.small | $30 |
| S3 | 100GB + requests | $10 |
| ALB | 1 load balancer | $20 |
| Data Transfer | Moderate | $20 |
| **Total** | | **$263-433/month** |

**Cost Optimization Tips:**
- Use spot instances for training (70% savings)
- Enable cluster autoscaler to scale down idle nodes
- Set S3 lifecycle policies (move to Glacier after 90 days)
- Use reserved instances for stable workloads (40% savings)

## Security Best Practices

1. **IRSA (IAM Roles for Service Accounts)**
   - Each pod gets only the permissions it needs
   - No shared credentials

2. **Private Subnets**
   - Database and training services in private subnets
   - Only API exposed via ALB

3. **Secrets Management**
   - Use AWS Secrets Manager or Kubernetes Secrets
   - Never commit secrets to Git

4. **Network Policies**
   - Restrict pod-to-pod communication
   - Whitelist only necessary traffic

5. **Image Scanning**
   - Enable ECR image scanning
   - Block vulnerable images in CI/CD

## Monitoring & Alerts

### Key Metrics to Monitor
- API latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Model prediction latency
- Training job success rate
- Data ingestion lag
- Resource utilization (CPU, memory)

### Recommended Alerts
- API error rate > 5%
- API latency p95 > 500ms
- Training job failures
- Data ingestion delays > 2 hours
- Model drift detected

## Troubleshooting

See [docs/runbook.md](runbook.md) for detailed troubleshooting steps.

## Cleanup

```bash
# Delete Kubernetes resources
kubectl delete -f infra/k8s/

# Delete Terraform infrastructure
cd infra/terraform
terraform destroy

# Delete S3 buckets (if needed)
aws s3 rb s3://quant-trading-raw-data --force
aws s3 rb s3://quant-trading-features --force
aws s3 rb s3://quant-trading-mlflow-artifacts --force
```
