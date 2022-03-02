from typing import Any
import boto3
from botocore.exceptions import ClientError
import json

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


def move_file(bucket: str, file: str, source: str, destination: str):
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

    try:
        s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
            CopySource=f"{bucket}/{source}/{file}"
        )
        s3_resource.Object(bucket, f"{source}/{file}").delete()
    except Exception as exc:
        print(
            f"Failed to move file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
        print(exc)
    else:
        print(
            f"Moved file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )


def copy_file(bucket: str, file: str, source: str, destination: str):
    """Copy `file` in `bucket` from `source` to `destination` folder

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    file : str
        Name of file to be copied (without full-path).
    source : str
        Source folder in S3 bucket.
    destination : str
        Destination folder in S3 bucket.
    """

    try:
        s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
            CopySource=f"{bucket}/{source}/{file}"
        )
    except Exception as exc:
        print(
            f"Failed to copy file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
    else:
        print(
            f"Copied file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )


def get_object(bucket: str, key: str) -> Any:
    """Gets object from S3.

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    key : str
        Key to file in bucket.

    Returns
    -------
    Any
        S3 Object retrieved.
    """
    try:
        s3_object = s3_client.get_object(Bucket=bucket, Key=key)
    except Exception:
        return None
    else:
        return s3_object


def put_object(json_object: str, bucket: str, key: str):
    """Puts `json_object` (in str) to S3 bucket.

    Parameters
    ----------
    json_object : str
        String representation of JSON object to put in S3.
    bucket : str
        S3 bucket name.
    key : str
        Key to file in bucket.
    """
    try:
        s3_client.put_object(Body=json.dumps(json_object), Bucket=bucket, Key=key)
    except Exception as exc:
        print(exc)


def create_presigned_url(
    bucket_name: str, object_name: str, expiration: int = 3600
) -> str:
    """Generate a presigned URL to share an S3 object

    Parameters
    ----------
    bucket_name : str
        Bucket name
    object_name : str
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

