output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.mlflow.endpoint
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value = {
    ingestion = aws_ecr_repository.ingestion.repository_url
    training  = aws_ecr_repository.training.repository_url
    api       = aws_ecr_repository.api.repository_url
  }
}

output "s3_buckets" {
  description = "S3 bucket names"
  value = {
    raw_data         = aws_s3_bucket.raw_data.id
    features         = aws_s3_bucket.features.id
    mlflow_artifacts = aws_s3_bucket.mlflow_artifacts.id
  }
}
