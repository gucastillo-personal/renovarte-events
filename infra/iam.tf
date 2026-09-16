# Policy least-privilege escrita a mano (en vez de la managed policy
# AWSLambdaBasicExecutionRole) a propósito: parte del valor de aprendizaje
# de este POC es entender exactamente qué permisos necesita la Lambda.

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "consumer" {
  name               = "${var.project_name}-consumer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "consumer_inline" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project_name}-consumer:*"]
  }

  statement {
    sid       = "ConsumeQueue"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.price_changes.arn]
  }
}

resource "aws_iam_role_policy" "consumer" {
  role   = aws_iam_role.consumer.id
  policy = data.aws_iam_policy_document.consumer_inline.json
}
