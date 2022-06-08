import boto3
from botocore.exceptions import ClientError
from src.config import SIGNED_URL_TIMEOUT
import os

s3_client = boto3.client("s3")


def get_audio_file(bucket: str, key: str, audio_extension: str) -> str:
    """Get corresponding audio file of JSON annotation (`key`) from AWS S3, in `bucket`.

    Args:
        bucket (str): Audio and JSON bucket name in S3.
        key (str): JSON file key name in S3.
        audio_extension (str): Audio extension.

    Returns:
        str: Pre-signed URL pointing to the audio file of the JSON annotation.
    """
    job_name = os.path.splitext(os.path.basename(key))[0]
    folder_name = os.path.basename(os.path.dirname(key))
    audio_file = f"dropbox/{folder_name}/{job_name}{audio_extension}"
    try:
        s3_source_signed_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": audio_file},
            ExpiresIn=SIGNED_URL_TIMEOUT,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        print(f"Failed to fetch key: {audio_file}")
        return None
    else:
        print(f"Successfully fetched {audio_file}")
        return s3_source_signed_url


def create_presigned_url(
    bucket_name: str, object_name: str, expiration: int = 3600
) -> str:
    """Generate a presigned URL to share an S3 object.

    Args:
        bucket_name (str): Bucket name
        object_name (str): Name of object/file
        expiration (int, optional): Time in seconds for the presigned URL to remain valid. Defaults to 3600.

    Returns:
        str: Presigned URL as string. If error, returns `None`.
    """
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as exc:
        print(exc)
        return None

    return response


def move_file(bucket: str, file: str, source: str, destination: str) -> None:
    """Move `file` in `bucket` from `source` to `destination` folder.

    Args:
        bucket (str): S3 bucket name.
        file (str): Name of file to be moved (without full-path).
        source (str): Source folder in S3 bucket.
        destination (str): Destination folder in S3 bucket.
    """
    s3_resource = boto3.resource("s3")

    try:
        s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
            CopySource=f"{bucket}/{source}/{file}"
        )
        s3_resource.Object(bucket, f"{source}/{file}").delete()
        print(
            f"Moved file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
    except Exception as exc:
        print(f"{bucket}/{source}/{file} not available")
