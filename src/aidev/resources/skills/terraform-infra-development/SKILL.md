# Terraform Infrastructure Development Skill

Building reliable infrastructure with Terraform (OpenTofu compatible).

## Overview

Terraform enables declarative infrastructure-as-code. This skill covers module design, state management, and production best practices.

## Module Structure

```
infra/
  modules/
    networking/
      main.tf
      variables.tf
      outputs.tf
      README.md
    compute/
      main.tf
      variables.tf
      outputs.tf
  environments/
    dev/
      main.tf
      terraform.tfvars
    prod/
      main.tf
      terraform.tfvars
  backend.tf
```

## Key Patterns

### Variables and Outputs

```hcl
# variables.tf
variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

# outputs.tf
output "instance_ip" {
  description = "Public IP of the instance"
  value       = aws_instance.main.public_ip
}
```

### Remote State

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

## Best Practices

1. **Use modules** for reusable infrastructure components
2. **Pin provider versions** to avoid unexpected upgrades
3. **Use remote state** with locking (S3 + DynamoDB)
4. **Tag all resources** consistently
5. **Separate environments** via workspaces or directories
6. **Use `terraform fmt`** and `terraform validate` in CI
7. **Review plans** before apply - never apply blindly
