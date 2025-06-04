resource "random_password" "db" {
  length  = 32
  special = true
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnet"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine         = "postgres"
  engine_version = "15"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "torah_db"
  username = "torah_user"
  password = var.db_password_override != "" ? var.db_password_override : random_password.db.result

  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  multi_az               = var.environment == "prod" ? true : false
  deletion_protection    = var.environment == "prod" ? true : false
  skip_final_snapshot    = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/${var.environment}/db_password"
  type  = "SecureString"
  value = var.db_password_override != "" ? var.db_password_override : random_password.db.result

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-password"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/${var.project_name}-${var.environment}-db/postgresql"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}
