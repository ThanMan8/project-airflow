resource "aws_s3_bucket" "managed-airflow-bucket" {
  bucket        = var.s3_bucket_name
  force_destroy = "false"

  tags = {
    Name          = "airflow-bucket-sw"
  }
}

resource "aws_s3_bucket_versioning" "managed-airflow-bucket-versioning" {
  bucket = aws_s3_bucket.managed-airflow-bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

