# ========================================
# MODULE RÉGION - INFRASTRUCTURE COMPLÈTE
# ========================================

# 1. VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name   = "CloudDiagnoze-VPC-${var.region_code}"
    Region = var.region_name
  }
}

# 2. Subnet Public 1
resource "aws_subnet" "public_subnet_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone = var.az_1

  tags = {
    Name   = "CloudDiagnoze-Subnet-1-${var.region_code}"
    Region = var.region_name
  }
}

# 3. Subnet Public 2
resource "aws_subnet" "public_subnet_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 2)
  availability_zone = var.az_2

  tags = {
    Name   = "CloudDiagnoze-Subnet-2-${var.region_code}"
    Region = var.region_name
  }
}

# 4. Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name   = "CloudDiagnoze-IGW-${var.region_code}"
    Region = var.region_name
  }
}

# 5. Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name   = "CloudDiagnoze-RT-${var.region_code}"
    Region = var.region_name
  }
}

# 6. Route Table Associations
resource "aws_route_table_association" "rta_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "rta_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# 7. Security Group EC2
resource "aws_security_group" "ec2_sg" {
  name        = "cloud-ec2-sg-${var.region_code}"
  description = "Security group for EC2 instances"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name   = "CloudDiagnoze-EC2-SG-${var.region_code}"
    Region = var.region_name
  }
}

# 8. Security Group RDS
resource "aws_security_group" "rds_sg" {
  name        = "cloud-rds-sg-${var.region_code}"
  description = "Allow PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name   = "CloudDiagnoze-RDS-SG-${var.region_code}"
    Region = var.region_name
  }
}

# 9. DB Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "cloud-diagnoze-subnet-group-${var.region_code}"
  subnet_ids = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

  tags = {
    Name   = "CloudDiagnoze-DB-Subnet-Group-${var.region_code}"
    Region = var.region_name
  }
}

# ========================================
# INSTANCES EC2 (5 par région - Mix T2/T3)
# ========================================

# Instance 0-1 : t3.micro
resource "aws_instance" "ec2_t3_micro" {
  count                       = 2
  ami                         = var.ec2_ami
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public_subnet_1.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true

  tags = {
    Name   = "CloudDiagnoze-EC2-${var.region_code}-t3micro-${count.index}"
    Region = var.region_name
    Type   = "t3.micro"
  }
}

# Instance 2 : t2.micro
resource "aws_instance" "ec2_t2_micro" {
  count                       = 1
  ami                         = var.ec2_ami
  instance_type               = "t2.micro"
  subnet_id                   = aws_subnet.public_subnet_1.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true

  tags = {
    Name   = "CloudDiagnoze-EC2-${var.region_code}-t2micro-0"
    Region = var.region_name
    Type   = "t2.micro"
  }
}

# Instance 3 : t2.nano
resource "aws_instance" "ec2_t2_nano" {
  count                       = 1
  ami                         = var.ec2_ami
  instance_type               = "t2.nano"
  subnet_id                   = aws_subnet.public_subnet_1.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true

  tags = {
    Name   = "CloudDiagnoze-EC2-${var.region_code}-t2nano-0"
    Region = var.region_name
    Type   = "t2.nano"
  }
}

# Instance 4 : t3.small
resource "aws_instance" "ec2_t3_small" {
  count                       = 1
  ami                         = var.ec2_ami
  instance_type               = "t3.small"
  subnet_id                   = aws_subnet.public_subnet_1.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true

  tags = {
    Name   = "CloudDiagnoze-EC2-${var.region_code}-t3small-0"
    Region = var.region_name
    Type   = "t3.small"
  }
}

# ========================================
# BUCKETS S3 (5 par région)
# ========================================

# Bucket générique 1
resource "aws_s3_bucket" "bucket_1" {
  bucket        = "clouddiagnoze-${var.region_code}-bucket-1-${var.random_id}"
  force_destroy = true

  tags = {
    Name   = "CloudDiagnoze-Bucket-1"
    Region = var.region_name
  }
}

# Bucket générique 2
resource "aws_s3_bucket" "bucket_2" {
  bucket        = "clouddiagnoze-${var.region_code}-bucket-2-${var.random_id}"
  force_destroy = true

  tags = {
    Name   = "CloudDiagnoze-Bucket-2"
    Region = var.region_name
  }
}

# Bucket logs
resource "aws_s3_bucket" "logs" {
  bucket        = "clouddiagnoze-${var.region_code}-logs-${var.random_id}"
  force_destroy = true

  tags = {
    Name        = "CloudDiagnoze-Logs"
    Region      = var.region_name
    Environment = "Production"
  }
}

# Bucket backups
resource "aws_s3_bucket" "backups" {
  bucket        = "clouddiagnoze-${var.region_code}-backups-${var.random_id}"
  force_destroy = true

  tags = {
    Name        = "CloudDiagnoze-Backups"
    Region      = var.region_name
    Environment = "Production"
  }
}

# Bucket static
resource "aws_s3_bucket" "static" {
  bucket        = "clouddiagnoze-${var.region_code}-static-${var.random_id}"
  force_destroy = true

  tags = {
    Name        = "CloudDiagnoze-Static"
    Region      = var.region_name
    Environment = "Production"
  }
}

# Chiffrement pour les buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  for_each = {
    logs    = aws_s3_bucket.logs.id
    backups = aws_s3_bucket.backups.id
    static  = aws_s3_bucket.static.id
  }

  bucket = each.value

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Versioning pour le bucket de backup
resource "aws_s3_bucket_versioning" "backup_versioning" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ========================================
# INSTANCE RDS (1 par région)
# ========================================

resource "aws_db_instance" "rds" {
  identifier             = "clouddiagnoze-db-${var.region_code}"
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "16.10"
  instance_class         = "db.t3.micro"
  db_name                = "diagdb"
  username               = "cloudadmin"
  password               = "DiagTest123!"
  skip_final_snapshot    = true
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name

  tags = {
    Name   = "CloudDiagnoze-RDS-${var.region_code}"
    Region = var.region_name
  }
}

