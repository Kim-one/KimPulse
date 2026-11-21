# KimPulse - infrastructure as code
#
# What this file creates (all on free tiers):
#   1. A resource group      - a folder that holds everything, so teardown is one command
#   2. An App Service plan   - the (free, F1) compute the app runs on
#   3. A Linux web app       - the Flask app itself
#
# How to use it (run from this infra/ folder):
#   az login                               # sign in to Azure
#   terraform init                         # download the Azure provider
#   terraform plan                         # preview what will be created
#   terraform apply                        # create it
#   terraform destroy                      # delete everything when you are done

terraform {
  required_version = ">= 1.6"

  required_providers {
    # The plugin that lets Terraform talk to Azure.
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    # Used only to generate a short random suffix (see below).
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  # Which Azure subscription to build in. Find yours with:
  #   az account show --query id -o tsv
  subscription_id = var.subscription_id
}

# ---------- Inputs ----------

variable "subscription_id" {
  description = "Azure subscription ID to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region. Canada Central (Toronto) is the closest to Halifax."
  type        = string
  default     = "canadacentral"
}

# ---------- Resources ----------

# Web app names must be unique across ALL of Azure, because they become
# <name>.azurewebsites.net. A random suffix avoids "name already taken" errors.
resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

# 1. Resource group: every resource below lives in here.
resource "azurerm_resource_group" "rg" {
  name     = "rg-kimpulse"
  location = var.location

  tags = {
    project = "kimpulse"
    purpose = "portfolio"
  }
}

# 2. App Service plan: the compute. F1 is the always-free tier.
#    Its limits (shared CPU, 60 CPU-minutes a day) are fine for a demo.
#    Do not change sku_name: any other value costs money.
resource "azurerm_service_plan" "plan" {
  name                = "plan-kimpulse"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "F1"
}

# 3. The web app that runs the Flask code.
resource "azurerm_linux_web_app" "app" {
  name                = "kimpulse-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  https_only = true # security basic: refuse plain http

  # Lets the GitHub Actions workflow deploy using a publish profile.
  # (A stronger setup is OIDC with a least-privilege identity - see README "Next steps".)
  webdeploy_publish_basic_authentication_enabled = true

  site_config {
    always_on = false # must be false on the free tier

    application_stack {
      python_version = "3.12"
    }

    # The command Azure runs to start the app.
    # "app:app" means: in app.py, use the Flask object named app.
    app_command_line = "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
  }

  app_settings = {
    # Tells Azure to run "pip install -r requirements.txt" when code is deployed.
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
  }

  tags = azurerm_resource_group.rg.tags
}

# ---------- Outputs (printed after "terraform apply") ----------

output "app_name" {
  description = "Use this as the AZURE_WEBAPP_NAME variable in GitHub"
  value       = azurerm_linux_web_app.app.name
}

output "app_url" {
  description = "Where the dashboard is live"
  value       = "https://${azurerm_linux_web_app.app.default_hostname}"
}
