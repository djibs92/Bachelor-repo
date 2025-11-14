variable "region_name" {
  description = "Nom de la région AWS (ex: eu-west-3)"
  type        = string
}

variable "region_code" {
  description = "Code court de la région (ex: paris, ireland, london)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block pour le VPC"
  type        = string
}

variable "az_1" {
  description = "Première availability zone"
  type        = string
}

variable "az_2" {
  description = "Deuxième availability zone"
  type        = string
}

variable "ec2_ami" {
  description = "AMI ID pour les instances EC2"
  type        = string
}

variable "random_id" {
  description = "Random ID pour noms uniques"
  type        = string
}

