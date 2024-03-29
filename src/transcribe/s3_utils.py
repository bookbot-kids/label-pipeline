# Copyright 2022 [PT BOOKBOT INDONESIA](https://bookbot.id/)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any
import boto3
from botocore.exceptions import ClientError
import json


class S3Client:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("s3", region_name=region_name)
        self.resource = boto3.resource("s3", region_name=region_name)

    def move_file(self, bucket: str, file: str, source: str, destination: str):
        """Move `file` in `bucket` from `source` to `destination` folder

        Args:
            bucket (str): S3 bucket name.
            file (str): Name of file to be moved (without full-path).
            source (str): Source folder in S3 bucket.
            destination (str): Destination folder in S3 bucket.
        """

        try:
            self.resource.Object(bucket, f"{destination}/{file}").copy_from(
                CopySource=f"{bucket}/{source}/{file}"
            )
            self.resource.Object(bucket, f"{source}/{file}").delete()
        except Exception as exc:
            print(
                f"Failed to move file from {bucket}/{source}/{file} to",
                f"{bucket}/{destination}/{file}",
            )
            print(exc)
        else:
            print(
                f"Moved file from {bucket}/{source}/{file} to",
                f"{bucket}/{destination}/{file}",
            )

    def copy_file(self, bucket: str, file: str, source: str, destination: str):
        """Copy `file` in `bucket` from `source` to `destination` folder

        Args:
            bucket (str): S3 bucket name.
            file (str): Name of file to be copied (without full-path).
            source (str): Source folder in S3 bucket.
            destination (str): Destination folder in S3 bucket.
        """

        try:
            self.resource.Object(bucket, f"{destination}/{file}").copy_from(
                CopySource=f"{bucket}/{source}/{file}"
            )
        except Exception:
            print(
                f"Failed to copy file from {bucket}/{source}/{file} to",
                f"{bucket}/{destination}/{file}",
            )
        else:
            print(
                f"Copied file from {bucket}/{source}/{file} to",
                f"{bucket}/{destination}/{file}",
            )

    def get_object(self, bucket: str, key: str) -> Any:
        """Gets object from S3.

        Args:
            bucket (str): S3 bucket name.
            key (str): Key to file in bucket.

        Returns:
            Any: S3 Object retrieved.
        """
        try:
            s3_object = self.client.get_object(Bucket=bucket, Key=key)
        except Exception:
            return None
        else:
            return s3_object

    def put_object(self, json_object: str, bucket: str, key: str):
        """Puts `json_object` (in str) to S3 bucket.

        Args:
            json_object (str): String representation of JSON object to put in S3.
            bucket (str): S3 bucket name.
            key (str): Key to file in bucket.
        """
        try:
            self.client.put_object(Body=json.dumps(json_object), Bucket=bucket, Key=key)
        except Exception as exc:
            print(exc)

    def create_presigned_url(
        self, bucket_name: str, object_name: str, expiration: int = 3600
    ) -> Any:
        """Generate a presigned URL to share an S3 object

        Args:
            bucket_name (str): Bucket name
            object_name (str): Name of object/file
            expiration (int, optional):
                Time (seconds) for the presigned URL to remain valid.
                Defaults to 3600.

        Returns:
            Any: Presigned URL as string. If error, returns `None`.
        """
        try:
            response = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError as exc:
            print(exc)
            return None

        return response
