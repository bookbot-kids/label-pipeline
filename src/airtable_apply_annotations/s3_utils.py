from typing import Callable, List
import boto3
from botocore.exceptions import ClientError

s3_resource = boto3.resource("s3")
s3_client = boto3.client("s3")


def write_file(bucket: str, file_content: str, destination: str, save_file_name):
    """Writes `file_content` to `save_file_name` to `bucket` at `destination` folder

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    file_content : str
        Content of file to write.
    destination : str
        Destination folder in S3 bucket.
    save_file_name : str
        Save file name
    """
    save_path = f"{destination}/{save_file_name}"
    try:
        s3_client.put_object(Body=file_content, Bucket=bucket, Key=save_path)
    except ClientError as exc:
        return


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
        print(
            f"Copied file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
    except ClientError as exc:
        return


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
        print(
            f"Moved file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
    except ClientError as exc:
        print(exc)


def delete_file(bucket: str, file: str, source: str):
    """Delete `file` in `bucket` from `source` folder

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    file : str
        Name of file to be deleted (without full-path).
    source : str
        Source folder in S3 bucket.
    """
    try:
        s3_resource.Object(bucket, f"{source}/{file}").delete()
        print(f"Deleted file from {bucket}/{source}/{file}")
    except ClientError as exc:
        return


def bulk_s3_actions(
    action: Callable,
    bucket: str,
    files: List[str],
    sources: List[str],
    targets: List[str] = None,
):
    """Applies a bulk S3 CRUD action for all `files` in `sources` and optionally, `targets`.

    Parameters
    ----------
    action : Callable
        Function calling an S3 CRUD operation.
    bucket : str
        S3 bucket name.
    files : List[str]
        List of files in `bucket`/`sources`
    sources : List[str]
        Source folders in `bucket`.
    targets : List[str], optional
        Target folders in `bucket`, by default None
    """
    if targets:
        assert len(sources) == len(targets)
        for source, target in zip(sources, targets):
            for file in files:
                action(bucket=bucket, file=file, source=source, destination=target)
    else:
        for source in sources:
            for file in files:
                action(bucket=bucket, file=file, source=source)
