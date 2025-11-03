output "ec2_public_ips" {
  value = aws_instance.web[*].public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.rds.endpoint
}

output "s3_bucket_names" {
  value = aws_s3_bucket.buckets[*].bucket
}