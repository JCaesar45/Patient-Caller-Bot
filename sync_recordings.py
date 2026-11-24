import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT") or None,
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET"],
    region_name=os.environ.get("S3_REGION", "auto"),
)
out = Path("recordings")
out.mkdir(exist_ok=True)
bucket = os.environ["S3_BUCKET"]
for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="recordings/"):
    for obj in page.get("Contents", []):
        dest = out / Path(obj["Key"]).name
        if not dest.exists():
            s3.download_file(bucket, obj["Key"], str(dest))
            print("downloaded", dest)
