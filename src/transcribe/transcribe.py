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

from enum import Enum, auto
from typing import Any, Dict, Tuple
import boto3
import time
import requests
from botocore.exceptions import ClientError
from config import REGION

transcribe_client = boto3.client("transcribe", region_name=REGION)


class TranscribeStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()


def get_job(client: boto3.session.Session.client, job_name: str) -> Dict[str, Any]:
    """Check if current job already exists

    Args:
        client (boto3.session.Session.client): AWS Transcribe client from boto3.
        job_name (str): Job name in AWS Transcribe.

    Returns:
        Dict[str, Any]:
            JSON-formatted response from AWS Transcribe, `None` on failure.
    """
    try:
        response = client.get_transcription_job(TranscriptionJobName=job_name)
        return response
    except ClientError:
        return None


def create_task(
    file_uri: str, job: Dict[str, Any]
) -> Tuple[TranscribeStatus, Dict[str, Any], Dict[str, Any]]:
    """Creates a JSON-formatted task for Label Studio from AWS Transcribe output.

    Args:
        file_uri (str): URI to audio file in S3 to be Transcribed.
        job (Dict[str, Any]): JSON-formatted response from AWS Transcribe.

    Returns:
        Tuple[TranscribeStatus, Dict[str, Any], Dict[str, Any]]:
            Tuple consisting of (1) status of AWS Transcribe job, (2) AWS Transcribe results and (3) JSON-formatted task for Label Studio
    """
    try:
        download_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        results = requests.get(download_uri).json()["results"]
        transcriptions = [r["transcript"] for r in results["transcripts"]]
        # confidence score for the entire phrase is a mean of confidence for individual words
        confidence = sum(
            float(item["alternatives"][0]["confidence"])
            for item in results["items"]
            if item["type"] == "pronunciation"
        ) / sum(1.0 for item in results["items"] if item["type"] == "pronunciation")
    except ZeroDivisionError as div_err:
        confidence = 0.0
    except Exception as exc:
        print(f"Error: {exc}")
        return (
            TranscribeStatus.FAILED,
            None,
            {
                "data": {"audio": file_uri},
                "predictions": [
                    {
                        "model_version": "amazon_transcribe",
                        "result": [
                            {
                                "from_name": "transcription",
                                "to_name": "audio",
                                "type": "textarea",
                                "value": {"text": [""]},
                            },
                        ],
                    }
                ],
            },
        )

    # if no exceptions occur, or if confidence is set to 0.0 after division-by-zero error
    return (
        TranscribeStatus.SUCCESS,
        results,
        {
            "data": {"audio": file_uri},
            "predictions": [
                {
                    "model_version": "amazon_transcribe",
                    "result": [
                        {
                            "from_name": "transcription",
                            "to_name": "audio",
                            "type": "textarea",
                            "value": {"text": transcriptions},
                        },
                    ],
                    "score": confidence,
                }
            ],
        },
    )


def transcribe_file(
    job_name: str,
    file_uri: str,
    media_format: str = "mp4",
    language_code: str = "en-US",
) -> Tuple[TranscribeStatus, Dict[str, Any]]:
    """Transcribes audio file with AWS Transcribe.

    Args:
        job_name (str): AWS Transcribe job name.
        file_uri (str): URI to audio file in S3 to be Transcribed.
        media_format (str, optional): Format of audio file. Defaults to "mp4".
        language_code (str, optional): AWS Transcribe language code of audio. Defaults to "en-US".

    Returns:
        Tuple[TranscribeStatus, Dict[str, Any]]: 
            Tuple consisting of (1) status of AWS Transcribe job and (2) JSON-formatted task for Label Studio
    """
    job = get_job(transcribe_client, job_name)
    if job:
        print(f"Transcription job {job_name} already exists.")
        return create_task(file_uri, job)

    # begin transcription job
    print(f"Start transcription job {job_name}")
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": file_uri},
        MediaFormat=media_format,
        LanguageCode=language_code,
    )

    # might be risky, but this relies on Lambda's 3 mins timeout
    while True:
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        if job_status in ["COMPLETED", "FAILED"]:
            print(f"Job {job_name} is {job_status}.")
            # if transcription job completes or fails, create Label Studio JSON-formatted task accordingly
            return create_task(file_uri, job)
        elif job_status == "IN_PROGRESS":
            # otherwise, if the transcription is still in progress, keep it running
            print(f"Waiting for {job_name}. Current status is {job_status}.")
            # give a 10 second timeout
            time.sleep(20)
