resource "aws_sns_topic" "price_changes" {
  name = "${var.project_name}-price-changes"
}
