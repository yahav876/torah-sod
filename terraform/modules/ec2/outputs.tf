output "autoscaling_group_name" {
  value = aws_autoscaling_group.main.name
}

output "launch_template_id" {
  value = aws_launch_template.main.id
}

output "launch_template_latest_version" {
  value = aws_launch_template.main.latest_version
}

output "launch_template_default_version" {
  value = aws_launch_template.main.default_version
}
