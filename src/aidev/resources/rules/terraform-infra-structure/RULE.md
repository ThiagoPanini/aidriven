# Terraform Infrastructure Structure Rules

Standards for organizing and writing Terraform code.

## Module Structure

Every Terraform module must have:

```
module-name/
  main.tf          # primary resources
  variables.tf     # input variables
  outputs.tf       # output values
  versions.tf      # provider and terraform version constraints
  README.md        # module documentation
```

## Naming Conventions

### Resources
```hcl
# Pattern: <resource_type>_<purpose>
resource "aws_s3_bucket" "application_assets" {}
resource "aws_security_group" "web_server" {}
```

### Variables
- Use snake_case
- Always include `description` and `type`
- Use `validation` blocks for constrained inputs

## State Management Rules

1. **Never commit `.tfstate` files** - always use remote state
2. **Enable state locking** - use DynamoDB for AWS backend
3. **Separate state per environment** - dev/staging/prod in different state files
4. **Enable encryption** - encrypt state at rest

## Version Pinning

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## Secrets Management

- Never hardcode secrets in `.tf` files
- Use `sensitive = true` on sensitive variables and outputs
- Reference secrets from AWS Secrets Manager or similar
- Use environment variables for provider credentials

## CI/CD Rules

1. Run `terraform fmt -check` on all PRs
2. Run `terraform validate` before plan
3. Run `terraform plan` on PRs (post as comment)
4. Only apply on merge to main
