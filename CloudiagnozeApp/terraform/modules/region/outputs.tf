output "vpc_id" {
  description = "ID du VPC"
  value       = aws_vpc.main.id
}

output "ec2_instance_ids" {
  description = "IDs des instances EC2"
  value = concat(
    aws_instance.ec2_t3_micro[*].id,
    aws_instance.ec2_t2_micro[*].id,
    aws_instance.ec2_t2_nano[*].id,
    aws_instance.ec2_t3_small[*].id
  )
}

output "ec2_public_ips" {
  description = "IPs publiques des instances EC2"
  value = concat(
    aws_instance.ec2_t3_micro[*].public_ip,
    aws_instance.ec2_t2_micro[*].public_ip,
    aws_instance.ec2_t2_nano[*].public_ip,
    aws_instance.ec2_t3_small[*].public_ip
  )
}

output "ec2_instance_types" {
  description = "Types des instances EC2"
  value = {
    t3_micro = length(aws_instance.ec2_t3_micro)
    t2_micro = length(aws_instance.ec2_t2_micro)
    t2_nano  = length(aws_instance.ec2_t2_nano)
    t3_small = length(aws_instance.ec2_t3_small)
  }
}

output "rds_endpoint" {
  description = "Endpoint de l'instance RDS"
  value       = aws_db_instance.rds.endpoint
}

output "s3_bucket_names" {
  description = "Noms des buckets S3"
  value = [
    aws_s3_bucket.bucket_1.bucket,
    aws_s3_bucket.bucket_2.bucket,
    aws_s3_bucket.logs.bucket,
    aws_s3_bucket.backups.bucket,
    aws_s3_bucket.static.bucket
  ]
}

