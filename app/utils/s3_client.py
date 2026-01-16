
import aioboto3
import io
import uuid
from app.core.config import settings
from botocore.exceptions import ClientError

class S3Client:
    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket_name = settings.S3_BUCKET_NAME
        self.session = aioboto3.Session()

    async def upload(self, file_data: bytes, content_type: str = "image/jpeg") -> str:
        """
        Uploads bytes to S3 and returns the public URL.
        """
        filename = f"{uuid.uuid4()}.jpg"
        
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3:
            try:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=io.BytesIO(file_data),
                    ContentType=content_type
                )
                # Ensure we return a valid accessible URL
                # For MinIO running locally, it might be http://localhost:9000/bucket/filename
                return f"{self.endpoint_url}/{self.bucket_name}/{filename}"
            except ClientError as e:
                print(f"Error uploading to S3: {e}")
                raise e

s3_client = S3Client()
