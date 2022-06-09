"""
Copyright 2022 [PT BOOKBOT INDONESIA](https://bookbot.id/)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import requests
import os
from urllib.parse import urljoin, urlparse
import boto3
from config import HOST, ADMIN_EMAIL, BUCKET

s3_client = boto3.client("s3")


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

    s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
        CopySource=f"{bucket}/{source}/{file}"
    )
    s3_resource.Object(bucket, f"{source}/{file}").delete()
    print(f"Moved file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}")


def lambda_handler(event, context):
    """Event listener for S3 event and checks if annotation has been verified by admin.

    Parameters
    ----------
    event : AWS Event
        A JSON-formatted document that contains data for a Lambda function to process.
    context : AWS Context
        An object that provides methods and properties that provide information about the invocation, function, and runtime environment.

    Returns
    -------
    Dict[str, Any]
        Response status code and success/error message.
    """
    response = json.loads(event["body"])
    action = response["action"]

    if action in ["ANNOTATION_CREATED", "ANNOTATION_UPDATED"]:
        task_id = response["annotation"]["task"]
        print(task_id)

        try:
            api_key = os.environ["LABEL_STUDIO_API_KEY"]
            headers = {"Authorization": f"Token {api_key}"}
            # get task in the event of annotation update/creation
            task = requests.get(f"{HOST}/api/tasks/{task_id}", headers=headers).json()
            print("Successfully received task from Label Studio.")
            print(task)
        except Exception as exc:
            error = f"Error: {exc}"
            print(error)
            return {"statusCode": 400, "body": json.dumps(error)}
        else:
            audio_url = task["data"]["audio"]
            audio_file = urljoin(audio_url, urlparse(audio_url).path)
            job_name = os.path.splitext(os.path.basename(audio_file))[0]
            folder_name = os.path.basename(os.path.dirname(audio_file))
            language = folder_name.split("-")[0]
            annotations = task["annotations"]

            archive_files = False

            # get all annotations
            for annotation in annotations:
                # if audio has been verified by admin of specific language
                if ADMIN_EMAIL[language] in annotation["created_username"]:
                    delete_path = (
                        f"label-studio/raw/{language}/{folder_name}/{job_name}.json"
                    )

                    # check if marked for archival by admin
                    for d in annotation["result"]:
                        if (
                            d["from_name"] == "deletion"
                            and d["value"]["choices"][0] == "Delete"
                        ):
                            archive_files = True

                    if archive_files:
                        # moves original audio and text to `archive`
                        for ext in ["aac", "txt"]:
                            move_file(
                                BUCKET,
                                f"{job_name}.{ext}",
                                f"dropbox/{folder_name}",
                                f"archive/{folder_name}",
                            )

                        # delete old raw JSONs from `label-studio/raw`
                        s3_client.delete_object(
                            Bucket=BUCKET, Key=delete_path,
                        )

                        # delete task from Label Studio
                        try:
                            requests.delete(
                                f"{HOST}/api/tasks/{task_id}", headers=headers
                            )
                        except Exception as exc:
                            error = f"Error: {exc}"
                            print(error)
                            return {"statusCode": 400, "body": json.dumps(error)}

                        deletion_message = f"Successfully archived task {task_id}."
                        print(deletion_message)
                        return {"statusCode": 200, "body": json.dumps(deletion_message)}
                    else:
                        # export verified JSON to `label-studio/verified`
                        save_path = (
                            f"label-studio/verified/{folder_name}/{job_name}.json"
                        )
                        s3_client.put_object(
                            Body=json.dumps(task).encode("utf8"),
                            Bucket=BUCKET,
                            Key=save_path,
                        )

                        # delete old raw JSONs from `label-studio/raw`
                        s3_client.delete_object(
                            Bucket=BUCKET, Key=delete_path,
                        )

                        verified_message = f"Transcription has been verified by administrator. File {save_path} successfully created; deleted old raw annotation from S3."
                        print(verified_message)
                        return {"statusCode": 200, "body": json.dumps(verified_message)}

            unverified_message = "Transcription has not been verified by administrator."
            print(unverified_message)

            return {
                "statusCode": 200,
                "body": json.dumps(unverified_message),
            }

