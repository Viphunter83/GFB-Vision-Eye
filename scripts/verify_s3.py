
import asyncio
import sys
from app.utils.s3_client import s3_client

async def test_s3():
    try:
        # Create a dummy image (just random bytes)
        dummy_data = b"fake_image_data_12345"
        
        print(f"Attempting upload to {s3_client.endpoint_url}/{s3_client.bucket_name}...")
        url = await s3_client.upload(dummy_data, content_type="text/plain")
        
        print(f"✅ Upload successful!")
        print(f"URL: {url}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_s3())
