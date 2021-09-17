import json
import requests
import os
from urllib.parse import urljoin, urlparse
import boto3
from config import HOST, ADMIN_EMAIL, BUCKET

s3_client = boto3.client("s3")


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
            annotations = task["annotations"]

            for annotation in annotations:
                audio_url = task["data"]["audio"]
                audio_file = urljoin(audio_url, urlparse(audio_url).path)
                job_name = os.path.splitext(os.path.basename(audio_file))[0]
                folder_name = os.path.basename(os.path.dirname(audio_file))
                language = folder_name.split("-")[0]

                # if audio has been verified by admin of specific language
                if ADMIN_EMAIL[language] in annotation["created_username"]:
                    # export JSON to `label-studio/verified`
                    save_path = f"label-studio/verified/{folder_name}/{job_name}.json"
                    s3_client.put_object(
                        Body=json.dumps(task).encode("utf8"),
                        Bucket=BUCKET,
                        Key=save_path,
                    )

                    verified_message = f"Transcription has been verified by administrator. File {save_path} successfully created."
                    print(verified_message)
                    return {"statusCode": 200, "body": json.dumps(verified_message)}

            unverified_message = "Transcription has not been verified by administrator."
            print(unverified_message)

            return {
                "statusCode": 200,
                "body": json.dumps(unverified_message),
            }

