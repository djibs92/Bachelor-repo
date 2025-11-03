provider "aws" {
  region = "eu-west-3"
}

resource "aws_instance" "web" {
  count         = 5
  ami           = "ami-0d8423e33dfb7aaea"
  instance_type = "t3.micro"
  
  # Ajouter ces configurations
  subnet_id     = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "CloudDiagnoze-EC2-${count.index}"
  }
}

resource "aws_s3_bucket" "buckets" {
  count  = 2
  bucket = "clouddiagnoze-bucket-${count.index}-${random_id.rand.hex}"
  force_destroy = true
}

resource "random_id" "rand" {
  byte_length = 4
}

# 1. Créer un VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true

  tags = {
    Name = "CloudDiagnoze-VPC"
  }
}

# 2. Créer un subnet public
resource "aws_subnet" "public_subnet" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-west-3a"

  tags = {
    Name = "CloudDiagnoze-Subnet"
  }
}

# Créer un deuxième subnet (requis pour RDS)
resource "aws_subnet" "public_subnet_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-3b"

  tags = {
    Name = "CloudDiagnoze-Subnet-2"
  }
}

# 3. Créer une Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "CloudDiagnoze-Gateway"
  }
}

# 4. Ajouter une route vers l'Internet
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "CloudDiagnoze-RouteTable"
  }
}

# 5. Attacher la route au subnet
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# 6. Créer un security group pour RDS
resource "aws_security_group" "rds_sg" {
  name        = "cloud-rds-sg"
  description = "Allow PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ⚠️ Pour tests seulement (à restreindre en prod)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "CloudDiagnoze-RDS-SG"
  }
}

# Créer un subnet group pour RDS
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "cloud-diagnoze-subnet-group"
  subnet_ids = [aws_subnet.public_subnet.id, aws_subnet.public_subnet_2.id]

  tags = {
    Name = "CloudDiagnoze-DB-Subnet-Group"
  }
}

# Ajouter un security group pour EC2
resource "aws_security_group" "ec2_sg" {
  name        = "cloud-ec2-sg"
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
    cidr_blocks = ["0.0.0.0/0"]  # ⚠️ En production, restreindre à votre IP
  }

  tags = {
    Name = "CloudDiagnoze-EC2-SG"
  }
}

resource "aws_db_instance" "rds" {
  allocated_storage   = 20
  engine             = "postgres"
  engine_version     = "17.4"  # Changer à une version disponible
  instance_class      = "db.t3.micro"
  db_name             = "diagdb"
  username            = "cloudadmin"
  password            = "DiagTest123!"
  skip_final_snapshot = true
  publicly_accessible = true
  
  # Ajouter ces configurations
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
}

# Nouveau bucket pour les logs
resource "aws_s3_bucket" "logs_bucket" {
  bucket = "clouddiagnoze-logs-${random_id.rand.hex}"
  force_destroy = true

  tags = {
    Name        = "CloudDiagnoze-Logs"
    Environment = "Production"
  }
}

# Nouveau bucket pour les backups
resource "aws_s3_bucket" "backup_bucket" {
  bucket = "clouddiagnoze-backups-${random_id.rand.hex}"
  force_destroy = true

  tags = {
    Name        = "CloudDiagnoze-Backups"
    Environment = "Production"
  }
}

# Nouveau bucket pour les données statiques
resource "aws_s3_bucket" "static_bucket" {
  bucket = "clouddiagnoze-static-${random_id.rand.hex}"
  force_destroy = true

  tags = {
    Name        = "CloudDiagnoze-Static"
    Environment = "Production"
  }
}

# Configuration du chiffrement pour les nouveaux buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  for_each = {
    logs   = aws_s3_bucket.logs_bucket.id
    backup = aws_s3_bucket.backup_bucket.id
    static = aws_s3_bucket.static_bucket.id
  }

  bucket = each.value

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Configuration du versioning pour le bucket de backup
resource "aws_s3_bucket_versioning" "backup_versioning" {
  bucket = aws_s3_bucket.backup_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}