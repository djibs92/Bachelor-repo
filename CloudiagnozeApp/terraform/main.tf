# ========================================
# TERRAFORM MULTI-RÉGIONS EU-WEST
# ========================================
# Provisionne l'infrastructure CloudDiagnoze dans 3 régions :
# - eu-west-1 (Irlande)
# - eu-west-2 (Londres)
# - eu-west-3 (Paris)

# Provider par défaut (eu-west-3)
provider "aws" {
  region = "eu-west-3"
}

# Provider pour eu-west-1 (Irlande)
provider "aws" {
  alias  = "ireland"
  region = "eu-west-1"
}

# Provider pour eu-west-2 (Londres)
provider "aws" {
  alias  = "london"
  region = "eu-west-2"
}

# Random ID pour noms uniques de buckets S3
resource "random_id" "rand" {
  byte_length = 4
}

# ========================================
# RÉGION 1 : EU-WEST-3 (PARIS)
# ========================================

module "paris" {
  source = "./modules/region"

  region_name = "eu-west-3"
  region_code = "paris"
  vpc_cidr    = "10.0.0.0/16"
  az_1        = "eu-west-3a"
  az_2        = "eu-west-3b"
  ec2_ami     = "ami-0d8423e33dfb7aaea" # Amazon Linux 2023 eu-west-3
  random_id   = random_id.rand.hex

  providers = {
    aws = aws
  }
}

# ========================================
# RÉGION 2 : EU-WEST-1 (IRLANDE)
# ========================================

module "ireland" {
  source = "./modules/region"

  region_name = "eu-west-1"
  region_code = "ireland"
  vpc_cidr    = "10.1.0.0/16"
  az_1        = "eu-west-1a"
  az_2        = "eu-west-1b"
  ec2_ami     = "ami-0d64bb532e0502c46" # Amazon Linux 2023 eu-west-1
  random_id   = random_id.rand.hex

  providers = {
    aws = aws.ireland
  }
}

# ========================================
# RÉGION 3 : EU-WEST-2 (LONDRES)
# ========================================

module "london" {
  source = "./modules/region"

  region_name = "eu-west-2"
  region_code = "london"
  vpc_cidr    = "10.2.0.0/16"
  az_1        = "eu-west-2a"
  az_2        = "eu-west-2b"
  ec2_ami     = "ami-0b9932f4918a00c4f" # Amazon Linux 2023 eu-west-2
  random_id   = random_id.rand.hex

  providers = {
    aws = aws.london
  }
}