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


class S3Client:
    def __init__(self, region_name="us-east-1"):
        """AWS S3 Client Constructor.

        Args:
            region_name (str, optional): AWS S3 region. Defaults to "us-east-1".
        """
        self.client = boto3.client("s3", region_name=region_name)
        self.resource = boto3.resource("s3", region_name=region_name)

    def get_object(self, bucket: str, key: str) -> Any:
        """Gets object from S3.

        Args:
            bucket (str): S3 bucket name.
            key (str): Key to file in bucket.

        Returns:
            Any: S3 Object retrieved.
        """
        try:
            s3_object = self.client.get_object(Bucket=bucket, Key=key)["Body"].read()
        except Exception:
            return None
        else:
            return s3_object
