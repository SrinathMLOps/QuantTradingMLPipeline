# Runbook & Troubleshooting

## Common Issues and Solutions

### 1. Data Ingestion Failures

#### Symptom: Ingestion CronJob failing

**Check logs:**
```bash
kubectl logs -l app=ingestion --tail=100
```

**Common causes:**

**A. Binance API rate limit exceeded**
```
Error: 429 Too Many Requests
```
Solution: Increase delay between requests or reduce frequency
```python
# In src/ingestion/fetch_data.py
time.sleep(2)  # Increase from 1 to 2 seconds
```

**B. Invalid API credentials**
```
Error: 401 Unauthorized
```
Solution: Update Kubernetes secret
```bash
kubectl delete secret binance-api
kubectl create secret generic binance-api \
  --from-literal=api-key=NEW_KEY \
  --from-literal=api-secret=NEW_SECRET
kubectl rollout restart cronjob/ingestion
```

**C. Network timeout**
```
Error: Connection timeout
```
Solution: Check network policies and increase timeout
```python
requests.get(url, timeout=30)  # Increase timeout
```

### 2. Training Job Failures

#### Symptom: Training pod in CrashLoopBackOff

**Check logs:**
```bash
kubectl logs -l app=training --tail=100
```

**Common causes:**

**A. Out of memory**
```
Error: Killed (OOM)
```
Solution: Increase memory limits
```yaml
# In k8s/training-deployment.yaml
resources:
  limits:
    memory: "8Gi"  # Increase from 4Gi
```

**B. Missing data**
```
Error: FileNotFoundError: data/features/BTCUSDT.parquet
```
Solution: Ensure feature engineering completed successfully
```bash
# Check S3 bucket
aws s3 ls s3://quant-trading-features/

# Manually trigger feature engineering
kubectl create job --from=cronjob/feature-engineering manual-features
```

**C. MLflow connection failed**
```
Error: Cannot connect to MLflow tracking server
```
Solution: Check MLflow service and database
```bash
kubectl get svc mlflow
kubectl logs -l app=mlflow

# Check database connection
kubectl exec -it mlflow-pod -- psql $DATABASE_URL -c "SELECT 1"
```

### 3. API Service Issues

#### Symptom: API returning 500 errors

**Check logs:**
```bash
kubectl logs -l app=api --tail=100
```

**Common causes:**

**A. Model not found**
```
Error: Model 'production' not found in registry
```
Solution: Promote a model to production
```python
import mlflow
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="xgboost-forecaster",
    version=1,
    stage="Production"
)
```

**B. High latency / timeout**
```
Error: Request timeout after 30s
```
Solution: Check model loading and caching
```bash
# Check if model is cached
kubectl exec -it api-pod -- ls /tmp/models/

# Increase timeout in ingress
kubectl edit ingress api-ingress
# Add: nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
```

**C. Pod not ready**
```
kubectl get pods -l app=api
# Shows 0/1 Ready
```
Solution: Check readiness probe
```bash
kubectl describe pod api-pod-xxx
# Look for "Readiness probe failed"

# Test health endpoint manually
kubectl exec -it api-pod -- curl localhost:8000/health
```

### 4. Monitoring & Alerts

#### Symptom: Prometheus not scraping metrics

**Check targets:**
```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Visit http://localhost:9090/targets
# Look for "DOWN" targets
```

**Solution: Fix service monitor**
```bash
kubectl get servicemonitor -n monitoring
kubectl describe servicemonitor api-metrics -n monitoring

# Ensure labels match
kubectl get svc api -o yaml | grep -A5 labels
```

#### Symptom: Grafana dashboard shows no data

**Check data source:**
```bash
# Login to Grafana (admin/prom-operator)
# Configuration > Data Sources > Prometheus
# Click "Test" button
```

**Solution: Reconnect data source**
```bash
# Delete and recreate Prometheus data source
# Or restart Grafana
kubectl rollout restart deployment/prometheus-grafana -n monitoring
```

### 5. Model Drift Detection

#### Symptom: Model performance degrading

**Check metrics:**
```bash
# Query Prometheus for prediction accuracy
# metric: model_prediction_accuracy

# Check MLflow for recent runs
mlflow ui
# Compare metrics across time
```

**Solution: Retrain model**
```bash
# Trigger training job manually
kubectl create job --from=cronjob/training manual-training-$(date +%s)

# Monitor training
kubectl logs -f job/manual-training-xxx
```

### 6. Database Issues

#### Symptom: MLflow metadata store unavailable

**Check RDS status:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier quant-trading-mlflow \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Check connectivity:**
```bash
kubectl run -it --rm debug --image=postgres:14 --restart=Never -- \
  psql $DATABASE_URL -c "SELECT 1"
```

**Solution: Restart RDS or check security groups**
```bash
# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --query 'SecurityGroups[0].IpPermissions'

# Ensure EKS nodes can reach RDS on port 5432
```

### 7. Storage Issues

#### Symptom: S3 access denied

**Check IAM permissions:**
```bash
# Verify IRSA is configured
kubectl describe sa api-service-account

# Check pod annotations
kubectl get pod api-pod-xxx -o yaml | grep iam.amazonaws.com

# Test S3 access from pod
kubectl exec -it api-pod -- aws s3 ls s3://quant-trading-features/
```

**Solution: Update IAM policy**
```bash
# Add S3 permissions to pod role
aws iam put-role-policy \
  --role-name quant-trading-api-role \
  --policy-name S3Access \
  --policy-document file://s3-policy.json
```

## Emergency Procedures

### Rollback Deployment

```bash
# Check deployment history
kubectl rollout history deployment/api

# Rollback to previous version
kubectl rollout undo deployment/api

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2
```

### Scale Down (Cost Saving)

```bash
# Scale down non-critical services
kubectl scale deployment/api --replicas=1
kubectl scale deployment/training --replicas=0

# Pause CronJobs
kubectl patch cronjob/ingestion -p '{"spec":{"suspend":true}}'
```

### Emergency Model Rollback

```python
import mlflow
client = mlflow.tracking.MlflowClient()

# Demote current production model
client.transition_model_version_stage(
    name="xgboost-forecaster",
    version=2,
    stage="Archived"
)

# Promote previous version
client.transition_model_version_stage(
    name="xgboost-forecaster",
    version=1,
    stage="Production"
)
```

## Health Check Commands

```bash
# Overall cluster health
kubectl get nodes
kubectl top nodes

# Application health
kubectl get pods --all-namespaces
kubectl get svc
kubectl get ingress

# Check recent events
kubectl get events --sort-by='.lastTimestamp' | tail -20

# Resource usage
kubectl top pods

# API health
curl http://YOUR_ALB_ENDPOINT/health

# MLflow health
curl http://mlflow-service:5000/health
```

## Useful Debugging Commands

```bash
# Get shell in pod
kubectl exec -it pod-name -- /bin/bash

# View logs with timestamps
kubectl logs pod-name --timestamps

# Follow logs
kubectl logs -f pod-name

# Previous container logs (after crash)
kubectl logs pod-name --previous

# Describe resource for events
kubectl describe pod pod-name

# Port forward for local testing
kubectl port-forward svc/api 8000:8000

# Copy files from pod
kubectl cp pod-name:/path/to/file ./local-file

# Run one-off job
kubectl run debug --rm -it --image=python:3.10 -- /bin/bash
```

## Monitoring Queries (PromQL)

```promql
# API request rate
rate(http_requests_total[5m])

# API error rate
rate(http_requests_total{status=~"5.."}[5m])

# API latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Model prediction latency
histogram_quantile(0.95, rate(model_prediction_duration_seconds_bucket[5m]))

# Pod CPU usage
sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)

# Pod memory usage
sum(container_memory_working_set_bytes) by (pod)
```

## Contact & Escalation

For critical issues:
1. Check this runbook first
2. Review recent deployments and changes
3. Check monitoring dashboards
4. Escalate to on-call engineer if unresolved
