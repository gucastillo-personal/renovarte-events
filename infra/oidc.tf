# OIDC para GitHub Actions: renovarte-pipeline asume este rol durante el
# workflow de publish para poder llamar sns:Publish, sin ninguna access key
# de larga duración guardada como secret. El thumbprint se resuelve
# dinámicamente (no se hardcodea) para no depender de que quede vigente.

data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions.certificates[0].sha1_fingerprint]
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Acotado al repo renovarte-pipeline (cualquier branch/ref dentro de
    # ese repo) — ningún otro repo de GitHub puede asumir este rol.
    #
    # GitHub arma el claim `sub` en dos formatos posibles: el clásico
    # "repo:OWNER/REPO:ref:..." o, cuando la cuenta/org tiene habilitados
    # los "immutable IDs" en el subject claim, "repo:OWNER@id/REPO@id:ref:...".
    # Se cubren ambos para no depender de esa configuración de GitHub.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repo}:*",
        "repo:${split("/", var.github_repo)[0]}@*/${split("/", var.github_repo)[1]}@*:*",
      ]
    }
  }
}

resource "aws_iam_role" "github_actions_producer" {
  name               = "${var.project_name}-github-actions-producer"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
}

data "aws_iam_policy_document" "github_actions_producer_inline" {
  statement {
    sid       = "PublishOnly"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.price_changes.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_producer" {
  role   = aws_iam_role.github_actions_producer.id
  policy = data.aws_iam_policy_document.github_actions_producer_inline.json
}
