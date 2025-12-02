SUPPORTED_PROVIDERS = ["aws"]

SUPPORTED_SERVICES_AWS = {"aws": ["ec2", "s3", "rds", "iam", "vpc"]}

SUPPORTED_AUTH_MODES = {
    "aws": ["sts"]  # Évolutif pour access_key, etc.
}