import pytest
import boto3
from moto import mock_aws
import io
from app.repositories.s3_repo import S3Repository


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_UPLOAD_BUCKET", "test-bucket")


@pytest.fixture
def mock_s3(aws_credentials):
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        yield s3


def test_upload_and_download_file(mock_s3):
    repo = S3Repository(bucket_name="test-bucket")

    file_content = b"test file content"
    file_obj = io.BytesIO(file_content)

    # Upload
    s3_key = "test_dir/file.txt"
    repo.upload_file(file_obj, s3_key)

    # Download
    downloaded_content = repo.download_file(s3_key)
    assert downloaded_content == file_content


def test_get_signed_url(mock_s3):
    repo = S3Repository(bucket_name="test-bucket")

    # Upload a file first
    s3_key = "test_dir/file2.txt"
    repo.upload_file(io.BytesIO(b"data"), s3_key)

    # Generate presigned URL
    url = repo.get_signed_url(s3_key, expires_in=3600)

    assert url is not None
    assert (
        "https://test-bucket.s3.amazonaws.com/test_dir/file2.txt" in url
        or "https://s3.amazonaws.com/test-bucket/test_dir/file2.txt" in url
    )
