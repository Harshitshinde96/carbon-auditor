import boto3
from typing import BinaryIO


from app.core.config import settings
from botocore.config import Config

class S3Repository:
    def __init__(self, bucket_name: str, region_name: str = None):
        self.bucket_name = bucket_name
        region = region_name or settings.AWS_REGION
        self.s3_client = boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))

    def upload_file(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Uploads a file-like object to S3."""
        self.s3_client.upload_fileobj(
            file_obj, self.bucket_name, s3_key, ExtraArgs={"ContentType": content_type}
        )

    def download_file(self, s3_key: str) -> bytes:
        """Downloads a file from S3 and returns its contents."""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response["Body"].read()

    def get_signed_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Generates a presigned URL for downloading a file."""
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=expires_in,
        )
