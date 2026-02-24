terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "quant-trading-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
  enable_dns_hostnames = true

  tags = {
    Project = var.project_name
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.project_name}-cluster"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }

    training = {
      desired_size = 0
      min_size     = 0
      max_size     = 3

      instance_types = ["c5.2xlarge"]
      capacity_type  = "SPOT"
    }
  }

  tags = {
    Project = var.project_name
  }
}

# RDS PostgreSQL for MLflow
resource "aws_db_instance" "mlflow" {
  identifier = "${var.project_name}-mlflow"

  engine         = "postgres"
  engine_version = "14"
  instance_class = "db.t3.small"

  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = "mlflow"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.mlflow.name

  skip_final_snapshot = true

  tags = {
    Project = var.project_name
  }
}

resource "aws_db_subnet_group" "mlflow" {
  name       = "${var.project_name}-mlflow"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Project = var.project_name
  }
}

resource "aws_security_group" "rds" {
  name   = "${var.project_name}-rds"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project_name
  }
}

# S3 Buckets
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data"

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket" "features" {
  bucket = "${var.project_name}-features"

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "${var.project_name}-mlflow-artifacts"

  tags = {
    Project = var.project_name
  }
}

# ECR Repositories
resource "aws_ecr_repository" "ingestion" {
  name = "${var.project_name}-ingestion"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_ecr_repository" "training" {
  name = "${var.project_name}-training"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_ecr_repository" "api" {
  name = "${var.project_name}-api"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project_name
  }
}

# IAM Role for Service Account (IRSA)
resource "aws_iam_role" "api_role" {
  name = "${var.project_name}-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = module.eks.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${module.eks.oidc_provider}:sub" = "system:serviceaccount:default:api-service-account"
        }
      }
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "api_s3_policy" {
  name = "s3-access"
  role = aws_iam_role.api_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.mlflow_artifacts.arn,
        "${aws_s3_bucket.mlflow_artifacts.arn}/*"
      ]
    }]
  })
}
