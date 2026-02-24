# AWS Setup Guide - High Level Overview

## What You'll Build

A production-grade cryptocurrency forecasting system on AWS that:
- Automatically fetches crypto data every hour
- Trains ML models with experiment tracking
- Serves predictions via REST API
- Scales automatically based on traffic
- Monitors performance with dashboards

## AWS Architecture Overview

```
Internet → ALB → EKS Cluster → Pods (API, Training, Ingestion)
                      ↓
                   RDS (MLflow metadata)
                      ↓
                   S3 (Data + Models)
```

## AWS Services You'll Use

### 1. EKS (Elastic Kubernetes Service) - $73/month
**What it does**: Runs your containers (API, training, data ingestion)
**Why**: Automatic scaling, easy deployment, industry standard

### 2. EC2 Instances - $60-200/month
**What it does**: Virtual servers that run your code
**Why**: 
- General pool (t3.medium): Always-on for API
- Training pool (c5.2xlarge spot): Only when training (70% cheaper)

### 3. RDS PostgreSQL - $30/month
**What it does**: Database for MLflow experiment tracking
**Why**: Managed backups, high availability, no maintenance

### 4. S3 Storage - $10/month
**What it does**: Stores data, features, and trained models
**Why**: Unlimited storage, cheap, durable

### 5. ALB (Application Load Balancer) - $20/month
**What it does**: Routes traffic to your API
**Why**: Health checks, SSL, automatic failover

### 6. ECR (Container Registry) - Free
**What it does**: Stores your Docker images
**Why**: Native AWS integration, secure

**Total Cost: $263-433/month** (can be reduced with reserved instances)

## Step-by-Step AWS Setup

### Phase 1: Prerequisites (15 minutes)

1. **Create AWS Account**
   - Go to aws.amazon.com
   - Sign up (free tier available)
   - Add payment method

2. **Install Tools**
   ```bash
   # AWS CLI
   pip install awscli
   
   # kubectl (Kubernetes CLI)
   # Download from kubernetes.io
   
   # Terraform
   # Download from terraform.io
   ```

3. **Configure AWS Credentials**
   ```bash
   aws configure
   # Enter Access Key ID
   # Enter Secret Access Key
   # Region: us-east-1
   ```

### Phase 2: Create Infrastructure with Terraform (30 minutes)

Terraform automates everything - no clicking in AWS console!

```bash
cd infra/terraform

# Initialize
terraform init

# Preview what will be created
terraform plan

# Create everything (takes 15-20 minutes)
terraform apply
```

**What Terraform Creates:**
- VPC with public/private subnets
- EKS cluster with 2 node groups
- RDS PostgreSQL database
- 3 S3 buckets (raw data, features, models)
- IAM roles and security groups
- ECR repositories for Docker images

### Phase 3: Deploy Application (20 minutes)

1. **Connect to EKS**
   ```bash
   aws eks update-kubeconfig --name quant-trading-cluster --region us-east-1
   kubectl get nodes  # Should show 2+ nodes
   ```

2. **Build and Push Docker Images**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   
   # Build images
   docker build -t quant-trading-api:latest -f docker/Dockerfile.api .
   
   # Tag and push
   docker tag quant-trading-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-api:latest
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/quant-trading-api:latest
   ```

3. **Create Secrets**
   ```bash
   kubectl create secret generic binance-api \
     --from-literal=api-key=YOUR_KEY \
     --from-literal=api-secret=YOUR_SECRET
   ```

4. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f infra/k8s/
   
   # Check status
   kubectl get pods
   kubectl get services
   ```

5. **Get API Endpoint**
   ```bash
   kubectl get ingress api-ingress
   # Copy the ADDRESS - this is your API URL
   ```

### Phase 4: Verify Everything Works (10 minutes)

```bash
# Test API
curl http://YOUR_ALB_ENDPOINT/health

# Check MLflow
kubectl port-forward svc/mlflow 5000:5000
# Open http://localhost:5000

# Check logs
kubectl logs -l app=api
```

## AWS Console - What to Check

### 1. EKS Dashboard
- Go to: AWS Console → EKS → Clusters
- Check: Cluster status = Active
- Check: Nodes = 2+ running

### 2. RDS Dashboard
- Go to: AWS Console → RDS → Databases
- Check: Status = Available
- Note: Endpoint (needed for MLflow)

### 3. S3 Dashboard
- Go to: AWS Console → S3
- Check: 3 buckets created
  - quant-trading-raw-data
  - quant-trading-features
  - quant-trading-mlflow-artifacts

### 4. EC2 Dashboard
- Go to: AWS Console → EC2 → Instances
- Check: 2+ instances running (EKS nodes)

### 5. Load Balancers
- Go to: AWS Console → EC2 → Load Balancers
- Check: ALB created by Kubernetes ingress
- Note: DNS name (your API endpoint)

## Architecture Diagram Explained

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              EKS Cluster (Kubernetes)                   │ │
│  │                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Ingestion    │  │  Training    │  │     API      │ │ │
│  │  │ (CronJob)    │  │  (Batch)     │  │  (Always On) │ │ │
│  │  │              │  │              │  │              │ │ │
│  │  │ Fetches data │  │ Trains model │  │ Serves preds │ │ │
│  │  │ every hour   │  │ with XGBoost │  │ via REST     │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │
│  │         │                  │                  │         │ │
│  └─────────┼──────────────────┼──────────────────┼─────────┘ │
│            │                  │                  │           │
│            ▼                  ▼                  ▼           │
│  ┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   S3 Buckets    │  │ RDS Postgres│  │  CloudWatch     │ │
│  │                 │  │             │  │  (Logs)         │ │
│  │ • Raw data      │  │ MLflow DB   │  │                 │ │
│  │ • Features      │  │             │  │                 │ │
│  │ • Models        │  │             │  │                 │ │
│  └─────────────────┘  └─────────────┘  └─────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              ALB (Load Balancer)                         │ │
│  │         your-api.us-east-1.elb.amazonaws.com            │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   Users     │
                         └─────────────┘
```

## Data Flow

1. **Ingestion** (Every hour)
   - CronJob wakes up
   - Fetches Bitcoin data from Binance
   - Saves to S3 bucket

2. **Feature Engineering** (After ingestion)
   - Reads raw data from S3
   - Calculates RSI, MACD, etc.
   - Saves features to S3

3. **Training** (Daily or on-demand)
   - Reads features from S3
   - Trains XGBoost model
   - Logs to MLflow (metrics, model)
   - Saves model to S3

4. **Inference** (Real-time)
   - User sends request to ALB
   - ALB routes to API pod
   - API loads model from MLflow
   - Returns prediction

## Monitoring

### Prometheus + Grafana
- Metrics: API latency, error rate, throughput
- Dashboards: Pre-built visualizations
- Alerts: Email/Slack when issues occur

### CloudWatch
- Logs from all pods
- Search and filter
- Set up alarms

## Cost Optimization Tips

1. **Use Spot Instances for Training** (70% savings)
   - Already configured in Terraform
   - Training nodes scale to zero when idle

2. **Enable Cluster Autoscaler**
   - Automatically removes idle nodes
   - Saves money during low traffic

3. **S3 Lifecycle Policies**
   - Move old data to Glacier after 90 days
   - Delete after 1 year

4. **Reserved Instances** (40% savings)
   - For stable workloads (API)
   - 1-year commitment

5. **Right-size Instances**
   - Start small (t3.medium)
   - Monitor and adjust

## Security Best Practices

1. **IRSA (IAM Roles for Service Accounts)**
   - Each pod gets only needed permissions
   - No shared credentials

2. **Private Subnets**
   - Database and training in private network
   - Only API exposed to internet

3. **Secrets Manager**
   - Store API keys securely
   - Rotate regularly

4. **Security Groups**
   - Whitelist only necessary traffic
   - Block everything else

## Troubleshooting

### Can't connect to EKS
```bash
aws eks update-kubeconfig --name quant-trading-cluster --region us-east-1
kubectl get nodes
```

### Pods not starting
```bash
kubectl describe pod POD_NAME
kubectl logs POD_NAME
```

### API not accessible
```bash
kubectl get ingress
# Wait 5-10 minutes for ALB to provision
```

### High costs
```bash
# Check running instances
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name]'

# Scale down
kubectl scale deployment/api --replicas=1
```

## Next Steps

1. **Set up CI/CD**
   - GitHub Actions already configured
   - Push code → Auto deploy

2. **Add Monitoring**
   - Install Prometheus + Grafana
   - Create dashboards

3. **Improve Model**
   - Add more features
   - Try LSTM
   - Hyperparameter tuning

4. **Add More Coins**
   - ETH, BNB, SOL
   - Multi-asset predictions

## Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

## Support

- AWS Support: support.aws.amazon.com
- Project Issues: github.com/SrinathMLOps/QuantTradingMLPipeline/issues
- Documentation: See `docs/` folder
