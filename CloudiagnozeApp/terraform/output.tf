# ========================================
# OUTPUTS MULTI-RÉGIONS
# ========================================

# EU-WEST-3 (PARIS)
output "paris_vpc_id" {
  description = "VPC ID Paris"
  value       = module.paris.vpc_id
}

output "paris_ec2_ips" {
  description = "IPs publiques EC2 Paris"
  value       = module.paris.ec2_public_ips
}

output "paris_rds_endpoint" {
  description = "RDS endpoint Paris"
  value       = module.paris.rds_endpoint
}

output "paris_s3_buckets" {
  description = "Buckets S3 Paris"
  value       = module.paris.s3_bucket_names
}

# EU-WEST-1 (IRLANDE)
output "ireland_vpc_id" {
  description = "VPC ID Irlande"
  value       = module.ireland.vpc_id
}

output "ireland_ec2_ips" {
  description = "IPs publiques EC2 Irlande"
  value       = module.ireland.ec2_public_ips
}

output "ireland_rds_endpoint" {
  description = "RDS endpoint Irlande"
  value       = module.ireland.rds_endpoint
}

output "ireland_s3_buckets" {
  description = "Buckets S3 Irlande"
  value       = module.ireland.s3_bucket_names
}

# EU-WEST-2 (LONDRES)
output "london_vpc_id" {
  description = "VPC ID Londres"
  value       = module.london.vpc_id
}

output "london_ec2_ips" {
  description = "IPs publiques EC2 Londres"
  value       = module.london.ec2_public_ips
}

output "london_rds_endpoint" {
  description = "RDS endpoint Londres"
  value       = module.london.rds_endpoint
}

output "london_s3_buckets" {
  description = "Buckets S3 Londres"
  value       = module.london.s3_bucket_names
}

# RÉSUMÉ GLOBAL
output "summary" {
  description = "Résumé de l'infrastructure déployée"
  value = {
    total_regions    = 3
    total_ec2        = 15
    total_s3_buckets = 15
    total_rds        = 3
    regions = [
      "eu-west-1 (Irlande)",
      "eu-west-2 (Londres)",
      "eu-west-3 (Paris)"
    ]
    ec2_types_per_region = {
      t3_micro = 2
      t2_micro = 1
      t2_nano  = 1
      t3_small = 1
    }
  }
}