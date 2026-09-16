resource "aws_sqs_queue" "price_changes_dlq" {
  name = "${var.project_name}-price-changes-dlq"
}

resource "aws_sqs_queue" "price_changes" {
  name                       = "${var.project_name}-price-changes"
  visibility_timeout_seconds = 30

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.price_changes_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue_policy" "allow_sns_publish" {
  queue_url = aws_sqs_queue.price_changes.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowSnsPublish"
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.price_changes.arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = aws_sns_topic.price_changes.arn }
      }
    }]
  })
}

resource "aws_sns_topic_subscription" "price_changes_to_sqs" {
  topic_arn            = aws_sns_topic.price_changes.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.price_changes.arn
  raw_message_delivery = true
}
