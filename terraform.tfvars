########################################
# RESOURCE GROUP
########################################

resource_groups = {
  infraguardian = {
    name     = "p-auea-infragai-rg"
    location = "Australia East"

    tags = {
      environment = "prod"
      owner       = "cloud-team"
      deployment  = "terraform"
    }
  }

  hubnetwork = {
    name     = "p-auea-hubnetwork-rg"
    location = "Australia East"

    tags = {
      environment = "prod"
      owner       = "cloud-team"
      deployment  = "terraform"
    }
  }
}

########################################
# APP SERVICE
########################################

app_services = {
  frontend = {
    app_service_plan_name = "p-auea-infraguardian-asp"
    app_service_name      = "p-auea-infraguardian-frontend"
    rg_key                = "infraguardian"
    subnet_key             = "frontend_infraguardian"
  }

  api = {
    app_service_plan_name = "p-auea-infraguardian-asp"
    app_service_name      = "p-auea-infraguardian-api"
    rg_key                = "infraguardian"
    subnet_key             = "api_infraguardian"
  }
}

########################################
# APP SERVICE VNET INTEGRATION
########################################

app_services_vnet_integration = {
  frontend = {
    appservice_key = "frontend"
    subnet_key     = "frontend_infraguardian"
  }

  api = {
    appservice_key = "api"
    subnet_key     = "api_infraguardian"
  }
}

########################################
# VNET
########################################

vnets = {
  hub = {
    name          = "p-auea-hub-vn"
    address_space = ["10.0.0.0/16"]
    rg_key        = "hubnetwork"
  }

  infraguardian = {
    name          = "p-auea-infraguardian-vn"
    address_space = ["10.1.0.0/16"]
    rg_key        = "infraguardian"
  }
}


########################################
# NSG
########################################

nsgs = {
  frontend_infraguardian = {
    name   = "p-auea-infraguardian-fe-nsg"
    rg_key = "infraguardian"
  }

  api_infraguardian = {
    name   = "p-auea-infraguardian-api-nsg"
    rg_key = "infraguardian"
  }
}

nsg_associations = {
  frontend_integration = {
    subnet_key = "frontend_infraguardian"
    nsg_key    = "frontend_infraguardian"
  }

  api_integration = {
    subnet_key = "api_infraguardian"
    nsg_key    = "api_infraguardian"
  }
}


########################################
# SUBNETS
########################################

subnets = {
  firewall_hub = {
    name             = "AzureFirewallSubnet"
    address_prefixes = ["10.0.1.0/24"]
    vnet_key         = "hub"
    rg_key           = "hubnetwork"
  }

  frontend_infraguardian = {
    name             = "p-auea-infraguardian-fe-sn"
    address_prefixes = ["10.1.0.0/24"]
    vnet_key          = "infraguardian"
    rg_key            = "infraguardian"

    delegation = {
      name    = "webapp"
      service = "Microsoft.Web/serverFarms"
    }
  }

  api_infraguardian = {
    name             = "p-auea-infraguardian-api-sn"
    address_prefixes = ["10.1.1.0/24"]
    vnet_key         = "infraguardian"
    rg_key            = "infraguardian"

    delegation = {
      name    = "webapp"
      service = "Microsoft.Web/serverFarms"
    }
  }

  pep_infraguardian = {
    name = "p-auea-infraguardian-pep-sn"
    address_prefixes = ["10.1.2.0/24"]
    vnet_key = "infraguardian"
    rg_key = "infraguardian"
  }
}


########################################
# STORAGE ACCOUNT
########################################

storage_accounts = {
  infraguardian = {
    name                       = "paueainfraguardianst"
    account_tier               = "Standard"
    account_replication_type   = "LRS"
    rg_key                     = "infraguardian"
  }
}


########################################
# KEY VAULT
########################################

key_vaults = {
  infraguardian = {
    name                       = "p-auea-infraguardian-kv"
    enabled_for_disk_encryption = true
    soft_delete_retention_days = 7
    purge_protection_enabled   = false
    sku_name                   = "standard"
    rbac_authorization_enabled = true
    rg_key                     = "infraguardian"
  }
}


########################################
# APP CONFIG
########################################

app_configs = {
  infraguardian = {
    name                    = "p-auea-infraguardian-ac"
    sku                     = "free"
    local_auth_enabled      = false
    public_network_access   = "enabled"
    purge_protection_enabled = false
    rg_key                  = "infraguardian"
  }
}


########################################
# SERVICE BUS
########################################

service_bus = {
  infraguardian = {
    name   = "p-auea-infraguardian-servicebus"
    sku    = "Basic"
    rg_key = "infraguardian"
  }
}

########################################
# DATABASE
########################################

sqlservers = {
  sqlserver_infraguardian = {
    name = "p-auea-infraguardian-sqlserver"
    version = "12.0"
    admin_login= "sqladmin"
    admin_password = "ReplaceWithSecurePassword123"
    rg_key = "infraguardian"
  }
}

sqldatabases = {
  sqldb_infraguardian = {
    name = "p-auea-infraguardian-sqldb"
    sku_name = "basic"
    server_key = "sqlserver_infraguardian"
  }
}


