## Move this backend file to your network config when migrating state
terraform {
  cloud {
    # Organization ID
    organization = "Deep_Dive_Terraform"
    # Workspace ID
    workspaces {
      name = "web-network-dev"
    }
  }
}