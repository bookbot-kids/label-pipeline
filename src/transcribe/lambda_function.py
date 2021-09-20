import boto3
from botocore.exceptions import ClientError
import requests
import time
import os
import json
from enum import Enum, auto
import re, string
from urllib.parse import unquote_plus
from config import LANGUAGE_CODES, BUCKET, REGION, HOST, STORAGE_ID

transcribe_client = boto3.client("transcribe", region_name=REGION)
s3_client = boto3.client("s3")


class TranscribeStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()


def get_language_code(filename):
    """Get language code from filename for transcribing

    Parameters
    ----------
    filename : str
        Audio filename with complete S3 path.

    Returns
    -------
    language_code : str
        Language code of the audio file, formatted for AWS Transcribe.
    """
    folder = os.path.basename(os.path.dirname(filename))
    language, country = folder.split("-")
    language_code = f"{language}-{country.upper()}"

    if language_code not in LANGUAGE_CODES:
        # defaults to US English and ID Indonesian if not supported
        return "en-US" if language == "en" else "id-ID"

    return language_code


def delete_job(client, job_name):
    """Deletes job if current job already exists

    Parameters
    ----------
    client : TranscribeService.Client
        AWS Transcribe client from boto3.
    job_name : str
        Job name in AWS Transcribe.

    Returns
    -------
    response: Dict[str, Any]
        JSON-formatted response from AWS Transcribe, `None` on failure.
    """
    try:
        response = client.delete_transcription_job(TranscriptionJobName=job_name)
        return response
    except ClientError:
        return None


def get_job(client, job_name):
    """Check if current job already exists

    Parameters
    ----------
    client : TranscribeService.Client
        AWS Transcribe client from boto3.
    job_name : str
        Job name in AWS Transcribe.

    Returns
    -------
    response: Dict[str, Any]
        JSON-formatted response from AWS Transcribe, `None` on failure.
    """
    try:
        response = client.get_transcription_job(TranscriptionJobName=job_name)
        return response
    except ClientError:
        return None


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


def init_label_studio_annotation():
    """Initializes a pair of dictionaries in Label Studio annotation format.

    Returns
    -------
    List[Dict[str, Any]]
        List containing pair of dictionaries in Label Studio JSON annotation format.
    """
    return [
        {
            "value": {"start": -1, "end": -1, "text": []},
            "id": "",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": -1, "end": -1, "labels": ["Sentence"]},
            "id": "",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
    ]


def segment(results):
    """Segments Amazon Transcribe raw output to individual sentences based on full-stop.

    Parameters
    ----------
    results : Dict[str, List]
        Resultant output received from AWS Transcribe.

    Returns
    -------
    output : List[Dict[str, Any]]
        List of dictionaries with segment-wise annotations for Label Studio.
    """
    output = []

    sentence_counter = 0
    new_sentence = True

    for item in results["items"]:
        # add a newly initialized pair of lists if new sentence is detected
        if new_sentence:
            output = output + init_label_studio_annotation()
            new_sentence = False

        idx = sentence_counter * 2

        text_dict = output[idx]
        label_dict = output[idx + 1]

        sentence_id = f"sentence_{sentence_counter}"
        text_dict["id"] = sentence_id
        label_dict["id"] = sentence_id

        text_values = text_dict["value"]
        label_values = label_dict["value"]

        token = item["alternatives"][0]["content"]

        if item["type"] == "pronunciation":
            # start time is at the first word of the sentence
            # end time is at the last word of the sentence
            for d in [text_values, label_values]:
                if d["start"] == -1:
                    d["start"] = float(item["start_time"])
                d["end"] = float(item["end_time"])

            # concat words in a sentence with whitespace
            text_values["text"] = [" ".join(text_values["text"] + [token])]

        elif item["type"] == "punctuation":
            # if `.` or `?` is detected, assume new sentence begins
            if token == "." or token == "?":
                sentence_counter += 1
                new_sentence = True
            # append any punctuation (`.` and `,`) to sentence
            text_values["text"] = ["".join(text_values["text"] + [token])]

    return output


def compare_transcriptions(ground_truth, transcribed_text):
    """Checks whether ground truth text and transcribed text are equal

    Parameters
    ----------
    ground_truth : str
        Ground truth text of audio.
    transcribed_text : str
        Transcribed text of audio generated by AWS Transcribe.

    Returns
    -------
    bool
        `True` if ground truth and transcribed texts are equal. `False` otherwise.
    """
    regex = re.compile("[%s]" % re.escape(string.punctuation))
    # remove punctuations, leading/trailing spaces, to lowercase
    ground_truth = regex.sub("", ground_truth).strip().lower()
    transcribed_text = regex.sub("", transcribed_text).strip().lower()
    return ground_truth == transcribed_text


def create_task(file_uri, job):
    """Creates a JSON-formatted task for Label Studio from AWS Transcribe output.

    Parameters
    ----------
    file_uri : str
        URI to audio file in S3 to be Transcribed.
    job : Dict[str, Any]
        JSON-formatted response from AWS Transcribe.

    Returns
    -------
    Tuple[TranscribeStatus, Dict[str, Any]]
        Tuple consisting of (1) status of AWS Transcribe job and (2) JSON-formatted task for Label Studio
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
        print(f"Error: {div_err}. Setting confidence to 0.0")
        confidence = 0.0
    except Exception as exc:
        print(f"Error: {exc}")
        return (
            TranscribeStatus.FAILED,
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
                        *segment(results),
                    ],
                    "score": confidence,
                }
            ],
        },
    )


def sync_label_studio_s3(language):
    """Syncs AWS S3 storage in Label Studio based on the project's `language`.

    Parameters
    ----------
    language : str
        Language of the labeling project, e.g. `en` or `id`.
    """
    # send sync signal to Label Studio project
    api_key = os.environ["LABEL_STUDIO_API_KEY"]
    headers = {"Authorization": f"Token {api_key}"}

    # hard code storage id since get_all_storages_s3 API is broken
    storage_id = STORAGE_ID[language]
    storage = requests.get(
        f"{HOST}/api/storages/s3/{storage_id}", headers=headers
    ).json()

    if storage:
        print(f"Successfully fetched storage {storage_id}. {storage}")

    sync = requests.post(
        f"{HOST}/api/storages/s3/{storage_id}/sync", headers=headers, data=storage
    ).json()

    if sync:
        print(f"Successfully synced storage {storage_id}. {sync}")


def transcribe_file(
    job_name, file_uri, transcribe_client, media_format="mp4", language_code="en-US"
):
    """Transcribes audio file with AWS Transcribe.

    Parameters
    ----------
    job_name : Dict[str, Any]
        JSON-formatted response from AWS Transcribe.
    file_uri : str
        URI to audio file in S3 to be Transcribed.
    transcribe_client : TranscribeService.Client
        AWS Transcribe client from boto3.
    media_format : str, optional
        Format of audio file, by default "mp4".
    language_code : str, optional
        AWS Transcribe language code of audio, by default "en-US".

    Returns
    -------
    Tuple[TranscribeStatus, Dict[str, Any]]
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


def lambda_handler(event, context):
    """Event listener for S3 event and calls Transcribe job.

    Parameters
    ----------
    event : AWS Event
        A JSON-formatted document that contains data for a Lambda function to process.
    context : AWS Context
        An object that provides methods and properties that provide information about the invocation, function, and runtime environment.

    Raises
    ------
    e
        Error message with key and bucket that causes error.
    """
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        print(e)
        print(
            "Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.".format(
                key, bucket
            )
        )
        raise e
    else:
        main(f"s3://{bucket}/{key}")


def main(audio_file):
    """Main function to run Transcribe, generate Label Studio JSON-annotation, and saves JSON to S3.

    Parameters
    ----------
    audio_file : str
        Audio filename with complete S3 path.
    """
    job_name = os.path.splitext(os.path.basename(audio_file))[0]
    folder_name = os.path.basename(os.path.dirname(audio_file))
    language = folder_name.split("-")[0]
    language_code = get_language_code(audio_file)

    status, task = transcribe_file(
        job_name,
        audio_file,
        transcribe_client,
        media_format="mp4",
        language_code=language_code,
    )

    transcribed_text = task["predictions"][0]["result"][0]["value"]["text"][0]
    ground_truth = ""

    if status == TranscribeStatus.SUCCESS:
        text_file_path = f"dropbox/{folder_name}/{job_name}.txt"
        try:
            # if successfully transcribed, get and compare with ground truth `.txt` file
            text_file = s3_client.get_object(Bucket=BUCKET, Key=text_file_path)
        except Exception as exc:
            print(f"Error: {exc}")
            print(f"Failed to fetch key: {text_file_path}")
        else:
            ground_truth = text_file["Body"].read().decode("utf-8")

    # add ground truth to Label Studio JSON-annotated task (for reference)
    task["data"]["text"] = ground_truth

    if status == TranscribeStatus.FAILED:
        # archive Transcribe-failed annotations
        save_path = f"archive/{folder_name}/{job_name}.json"
        # move audios to `archive`
        for ext in ["aac", "txt"]:
            move_file(
                BUCKET,
                f"{job_name}.{ext}",
                f"dropbox/{folder_name}",
                f"archive/{folder_name}",
            )
    elif not compare_transcriptions(ground_truth, transcribed_text):
        # save Label Studio-ready annotations to `label-studio/raw/{language}/` for further inspection
        save_path = f"label-studio/raw/{language}/{folder_name}/{job_name}.json"
    else:
        # otherwise, save annotations to `label-studio/verified` for audio splitting
        save_path = f"label-studio/verified/{folder_name}/{job_name}.json"

    # export JSON to respective folders in S3
    s3_client.put_object(Body=json.dumps(task), Bucket=BUCKET, Key=save_path)
    print(f"File {save_path} successfully created and saved.")
