output "sns_topic_arn" {
  description = "ARN del topic SNS al que el producer publica los eventos."
  value       = aws_sns_topic.price_changes.arn
}

output "sqs_queue_url" {
  description = "URL de la cola SQS principal (para inspección manual)."
  value       = aws_sqs_queue.price_changes.id
}

output "sqs_dlq_url" {
  description = "URL de la dead-letter queue."
  value       = aws_sqs_queue.price_changes_dlq.id
}

output "lambda_function_name" {
  description = "Nombre de la función Lambda (para ver logs con `aws logs tail`)."
  value       = aws_lambda_function.consumer.function_name
}
