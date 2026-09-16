variable "aws_region" {
  description = "Región AWS donde se crean los recursos."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefijo usado para nombrar todos los recursos."
  type        = string
  default     = "renovarte-events"
}

variable "discord_webhook_url" {
  description = "Webhook de Discord al que la Lambda envía las notificaciones. Sin default a propósito: va en terraform.tfvars, local y gitignoreado."
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "Repo de GitHub (org/nombre) autorizado a asumir el rol de OIDC para publicar eventos desde CI."
  type        = string
  default     = "gucastillo-personal/renovarte-pipeline"
}
