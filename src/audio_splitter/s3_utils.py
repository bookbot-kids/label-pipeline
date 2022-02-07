import boto3
from botocore.exceptions import ClientError
from config import SIGNED_URL_TIMEOUT
import os

s3_client = boto3.client("s3")


def get_audio_file(bucket, key, audio_extension):
    """Get corresponding audio file of JSON annotation (`key`) from AWS S3, in `bucket`.

    Parameters
    ----------
    bucket : str
        Audio and JSON bucket name in S3.
    key : str
        JSON file key name in S3.

    Returns
    -------
    s3_source_signed_url: str
        Pre-signed URL pointing to the audio file of the JSON annotation.
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


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    Parameters
    ----------
    bucket_name : string
        Bucket name
    object_name : string
        Name of object/file
    expiration : int, optional
        Time in seconds for the presigned URL to remain valid, by default 3600

    Returns
    -------
    str
        Presigned URL as string. If error, returns None.
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


def move_file(bucket, file, source, destination):
    """Move `file` in `bucket` from `source` to `destination` folder

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    file : str
        Name of file to be moved (without full-path).
    source : str
        Source folder in S3 bucket.
    destination : str
        Destination folder in S3 bucket.
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
