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

import boto3

s3_client = boto3.client("s3")


def get_audio_file(audio_url: str):
    """Get audio file from AWS S3, in `bucket`.

    Args:
        audio_url (str): Audio url in S3.

    Raises:
        exc: Error fetching file.

    Returns:
        _type_: Pre-signed URL pointing to the audio file of the JSON annotation.
    """
    audio_url = audio_url.replace("s3://", "")
    bucket, key = audio_url.split("/", 1)
    try:
        s3_source_signed_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
    except Exception as exc:
        print(f"Failed to fetch key: {key}")
        raise exc
    else:
        return s3_source_signed_url
