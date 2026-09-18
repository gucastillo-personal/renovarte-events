data "archive_file" "consumer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../consumer/src"
  output_path = "${path.module}/build/consumer.zip"
}

resource "aws_lambda_function" "consumer" {
  function_name    = "${var.project_name}-consumer"
  role             = aws_iam_role.consumer.arn
  handler          = "handler.handler"
  runtime          = "nodejs22.x"
  filename         = data.archive_file.consumer_zip.output_path
  source_code_hash = data.archive_file.consumer_zip.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      DISCORD_WEBHOOK_URL = var.discord_webhook_url
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_to_consumer" {
  event_source_arn        = aws_sqs_queue.price_changes.arn
  function_name           = aws_lambda_function.consumer.arn
  batch_size              = 10
  function_response_types = ["ReportBatchItemFailures"]
}
