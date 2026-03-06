import boto3
import time
import os
from dotenv import load_dotenv
load_dotenv()
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_KEY")
REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("S3_BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)


def upload_to_s3(file_path, object_name):
    start_time = time.perf_counter()

    s3.upload_file(file_path, BUCKET_NAME, object_name)

    upload_time = time.perf_counter() - start_time
    print(f"Upload completed in {upload_time:.4f} seconds")

    return upload_time


def download_from_s3(object_name, download_path):
    start_time = time.perf_counter()

    s3.download_file(BUCKET_NAME, object_name, download_path)

    download_time = time.perf_counter() - start_time
    print(f"Download completed in {download_time:.4f} seconds")

    return download_time