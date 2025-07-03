resource "aws_iam_role" "lambda_exec_cost_optimizer_role" {
  name                 = "IAM_lambda_Cost_Optimizer-tf"
  max_session_duration = 3600
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_cost_optimizer_policy" {
  name = "IAM_lambda_cost_optimizer_policy-tf"
  role = aws_iam_role.lambda_exec_cost_optimizer_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:*",
          "ec2:DescribeAddresses",
          "ec2:DescribeSnapshots",
          "ec2:DescribeVolumes",
          "ec2:DescribeInstances",
          "ec2:DeleteVolume",
          "ec2:DeleteSnapshot",
          "ec2:ReleaseAddress",
          "ec2:DisassociateAddress",
          "ec2:StartInstances",
          "ec2:StopInstances"
        ],
        Resource = "*"
      }
    ]
  })
}

// start stop ec2 lambda
resource "aws_lambda_function" "start_stop_instance" {
  function_name = "start-stop-instance-tf"
  runtime       = "python3.13"
  role          = aws_iam_role.lambda_exec_cost_optimizer_role.arn
  handler       = "start-stop-instance-dev.lambda_handler"

  filename         = data.archive_file.lambda-start_stop_instance_zip.output_path
  source_code_hash = data.archive_file.lambda-start_stop_instance_zip.output_base64sha256

  timeout = 10
}

data "archive_file" "lambda-start_stop_instance_zip" {
  type        = "zip"
  source_file = "${path.module}/start-stop-instance-dev.py"
  output_path = "${path.module}/start-stop-instance-dev.zip"
}



// clean redundant resources
resource "aws_lambda_function" "delete_redundant_resources" {
  function_name = "delete-redundant-resource-tf"
  runtime       = "python3.13"
  role          = aws_iam_role.lambda_exec_cost_optimizer_role.arn
  handler       = "clean-redundant-resources.lambda_handler"

  filename         = data.archive_file.lambda_delete_resources_zip.output_path
  source_code_hash = data.archive_file.lambda_delete_resources_zip.output_base64sha256

  timeout = 10
}

data "archive_file" "lambda_delete_resources_zip" {
  type        = "zip"
  source_file = "${path.module}/clean-redundant-resources.py"
  output_path = "${path.module}/clean-redundant-resources.zip"
}

// Trigger for start instance
resource "aws_cloudwatch_event_rule" "trigger_start_instance" {
  name                = "daily-lambda-trigger-start-instance"
  description         = "Triggers Lambda daily to start ec2 instance"
  schedule_expression = "cron(30 2 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_start_target" {
  rule      = aws_cloudwatch_event_rule.trigger_start_instance.name
  target_id = "startlambda"
  arn       = aws_lambda_function.start_stop_instance.arn

  input = jsonencode({
    action = "start"
  })
}

resource "aws_lambda_permission" "allow_start_cloudwatch" {
  statement_id  = "AllowStopStartCloudwatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start_stop_instance.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_start_instance.arn
}



// Trigger for stop instance
resource "aws_cloudwatch_event_rule" "trigger_stop_instance" {
  name                = "daily-lambda-trigger-stop-instance"
  description         = "Triggers Lambda daily to stop ec2 instance"
  schedule_expression = "cron(30 16 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_stop_target" {
  rule      = aws_cloudwatch_event_rule.trigger_stop_instance.name
  target_id = "stoplambda"
  arn       = aws_lambda_function.start_stop_instance.arn

  input = jsonencode({
    action = "stop"
  })
}

resource "aws_lambda_permission" "allow_stop_cloudwatch" {
  statement_id  = "AllowStopFromCloudwatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start_stop_instance.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_stop_instance.arn
}

// Trigger for deleting redundant resources
resource "aws_cloudwatch_event_rule" "trigger_delete_redundant_resources" {
  name                = "daily-lambda-trigger-delete-redundant-resources"
  description         = "Triggers Lambda daily to stop ec2 instance"
  schedule_expression = "cron(30 17 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_delete_redundant_resources_target" {
  rule      = aws_cloudwatch_event_rule.trigger_delete_redundant_resources.name
  target_id = "deleteresourcelambda"
  arn       = aws_lambda_function.delete_redundant_resources.arn
}

resource "aws_lambda_permission" "allow_delete_redundant_resources_cloudwatch" {
  statement_id  = "AllowDeleteFromCloudwatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete_redundant_resources.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_delete_redundant_resources.arn
}