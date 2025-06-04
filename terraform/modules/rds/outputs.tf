output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "db_host" {
  value = aws_db_instance.main.address
}

output "db_name" {
  value = aws_db_instance.main.db_name
}

output "db_username" {
  value = aws_db_instance.main.username
}

output "db_password_ssm_parameter" {
  value = aws_ssm_parameter.db_password.name
}
