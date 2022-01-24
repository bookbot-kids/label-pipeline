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
from operator import itemgetter
from itertools import groupby
from math import ceil
from homophones import HOMOPHONES, match_sequence
from mispronunciation import detect_mispronunciation
from srt2txt import srt2txt

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


def copy_file(bucket, file, source, destination):
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
    s3_resource = boto3.resource("s3")

    s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
        CopySource=f"{bucket}/{source}/{file}"
    )
    print(f"Copied file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}")


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
        {
            "value": {"start": -1, "end": -1, "text": []},
            "id": "",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
    ]


def sentencewise_segment(results, ground_truth):
    """Segments Amazon Transcribe raw output to individual sentences based on full-stop.

    Parameters
    ----------
    results : Dict[str, List]
        Resultant output received from AWS Transcribe.
    ground_truth : str
        Ground truth text for the corresponding annotation.

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

        idx = sentence_counter * 3

        text_dict = output[idx]
        label_dict = output[idx + 1]
        ground_truth_dict = output[idx + 2]

        sentence_id = f"sentence_{sentence_counter}"
        text_dict["id"] = sentence_id
        label_dict["id"] = sentence_id
        ground_truth_dict["id"] = sentence_id

        text_values = text_dict["value"]
        label_values = label_dict["value"]
        ground_truth_values = ground_truth_dict["value"]

        token = item["alternatives"][0]["content"]

        if item["type"] == "pronunciation":
            # start time is at the first word of the sentence
            # end time is at the last word of the sentence
            for d in [text_values, label_values, ground_truth_values]:
                if d["start"] == -1:
                    d["start"] = float(item["start_time"])
                d["end"] = float(item["end_time"])

            # concat words in a sentence with whitespace
            text_values["text"] = [" ".join(text_values["text"] + [token])]
            # provide region-wise ground truth for convenience
            ground_truth_values["text"] = [ground_truth]

        elif item["type"] == "punctuation":
            # if `.` or `?` is detected, assume new sentence begins
            if token == "." or token == "?":
                sentence_counter += 1
                new_sentence = True
            # append any punctuation (`.` and `,`) to sentence
            text_values["text"] = ["".join(text_values["text"] + [token])]

    return output


def overlapping_segments(results, ground_truth, language, max_repeats=None):
    """Segments Amazon Transcribe raw output to individual sentences based on overlapping regions.

    Parameters
    ----------
    results : Dict[str, List]
        Resultant output received from AWS Transcribe.
    ground_truth : str
        Ground truth text for the corresponding annotation.
    language : str
        Language of the transcript-ground truth pair.
    max_repeats : int, optional
        Maximum number of repeats when detecting for overlaps, by default None.

    Returns
    -------
    output : List[Dict[str, Any]]
        List of dictionaries with segment-wise annotations for Label Studio.
    """
    output = []
    sentence_counter = 0

    transcripts = [
        item["alternatives"][0]["content"].lower().strip() for item in results["items"]
    ]

    ground_truth = ground_truth.lower().strip().replace("-", " ").split(" ")

    # gets approximate number of repeats for case where len(ground_truth) << len(transcripts)
    # multiplier also manually tweakable if needed, e.g. 3
    multiplier = (
        max_repeats if max_repeats else ceil(len(transcripts) / len(ground_truth))
    )
    ground_truth *= multiplier

    # find overlaps and mark as new sequence
    homophones = HOMOPHONES[language] if language in HOMOPHONES else None
    aligned_transcripts, _ = match_sequence(transcripts, ground_truth, homophones)

    for _, g in groupby(enumerate(aligned_transcripts), lambda x: x[0] - x[1]):
        # add a newly initialized pair of lists if new sequence is detected
        seq = list(map(itemgetter(1), g))
        output = output + init_label_studio_annotation()

        idx = sentence_counter * 3

        text_dict = output[idx]
        label_dict = output[idx + 1]
        ground_truth_dict = output[idx + 2]

        sentence_id = f"sentence_{sentence_counter}"
        text_dict["id"] = sentence_id
        label_dict["id"] = sentence_id
        ground_truth_dict["id"] = sentence_id

        text_values = text_dict["value"]
        label_values = label_dict["value"]
        ground_truth_values = ground_truth_dict["value"]

        # first and last element of the sequence
        first, last = seq[0], seq[-1]

        # start time is at the first word of the sequence
        # end time is at the last word of the sequence
        for d in [text_values, label_values, ground_truth_values]:
            d["start"] = float(results["items"][first]["start_time"])
            d["end"] = float(results["items"][last]["end_time"])

        # concat words in a sequence with whitespace
        overlap = [" ".join(transcripts[first : last + 1])]
        # provide region-wise transcription and ground truth for convenience
        for d in [text_values, ground_truth_values]:
            d["text"] = overlap

        sentence_counter += 1

    return output


def classify_mispronunciation(results, ground_truth, language):
    """Classifies if a transcription result and ground truth text is a case of mispronunciation.

    Parameters
    ----------
    results : Dict[str, List]
        Resultant output received from AWS Transcribe.
    ground_truth : str
        Ground truth text for the corresponding annotation.
    language : str
        Language of the transcript-ground truth pair.

    Returns
    -------
    bool
        True if there is a mispronunciation. False otherwise.
    """
    transcripts = [
        item["alternatives"][0]["content"]
        .replace("-", " ")
        .translate(str.maketrans("", "", string.punctuation))
        .lower()
        .strip()
        for item in results["items"]
    ]

    ground_truth = (
        ground_truth.replace("-", " ")
        .translate(str.maketrans("", "", string.punctuation))
        .lower()
        .strip()
        .split(" ")
    )

    homophones = HOMOPHONES[language] if language in HOMOPHONES else None

    is_mispronunciation = detect_mispronunciation(ground_truth, transcripts, homophones)

    return is_mispronunciation


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
    Tuple[TranscribeStatus, Dict[str, Any], Dict[str, Any]]
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
        print(f"Error: {div_err}. Setting confidence to 0.0")
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
    EXT2FORMAT = {".wav": "wav", ".m4a": "mp4", ".aac": "mp4"}
    job_name, audio_extension = os.path.splitext(os.path.basename(audio_file))
    folder_name = os.path.basename(os.path.dirname(audio_file))
    language = folder_name.split("-")[0]
    language_code = get_language_code(audio_file)

    status, results, task = transcribe_file(
        job_name,
        audio_file,
        transcribe_client,
        media_format=EXT2FORMAT[audio_extension],
        language_code=language_code,
    )

    # is_from_youtube = folder_name.split("-")[1] == "youtube"

    transcribed_text = task["predictions"][0]["result"][0]["value"]["text"][0]
    ground_truth = ""
    # flag to indicate if txt ground truth can be found; otherwise, consult srt file
    # this avoids having to attempt to get BOTH txt and srt from S3
    is_text_file_available = False
    is_mispronunciation = False

    if status == TranscribeStatus.SUCCESS:
        # try and find corresponding txt ground truth file
        text_file_path = f"dropbox/{folder_name}/{job_name}.txt"
        try:
            # if successfully transcribed, get and compare with ground truth `.txt` file
            text_file = s3_client.get_object(Bucket=BUCKET, Key=text_file_path)
        except Exception as exc:
            print(
                f"Key {text_file_path} is unavailable, will attempt to grab `srt` file.."
            )
        else:
            is_text_file_available = True
            ground_truth = text_file["Body"].read().decode("utf-8")
            # classify for mispronunciation
            is_mispronunciation = classify_mispronunciation(
                results, ground_truth, language=language
            )
            # add region-wise transcriptions and ground truth (for convenience of labeler)
            task["predictions"][0]["result"] += overlapping_segments(
                results, ground_truth, language=language, max_repeats=3
            )

        if not is_text_file_available:
            # otherwise, try and find the corresponding srt ground truth file
            srt_file_path = f"dropbox/{folder_name}/{job_name}.srt"
            try:
                # if successfully transcribed, get and compare with ground truth `.srt` file
                srt_file = s3_client.get_object(Bucket=BUCKET, Key=srt_file_path)
            except Exception as exc:
                print(f"Key {srt_file_path} is also unavailable..")
            else:
                # convert srt to txt
                ground_truth = srt2txt(srt_file["Body"].read().decode("utf-8"))
                # classify for mispronunciation
                is_mispronunciation = classify_mispronunciation(
                    results, ground_truth, language=language
                )
                # add region-wise transcriptions and ground truth (for convenience of labeler)
                task["predictions"][0]["result"] += overlapping_segments(
                    results, ground_truth, language=language, max_repeats=3
                )

    # add ground truth to Label Studio JSON-annotated task (for reference)
    task["data"]["text"] = ground_truth

    if status == TranscribeStatus.FAILED or transcribed_text == "":
        # archive Transcribe-failed annotations
        save_path = f"archive/{folder_name}/{job_name}.json"

        # move audios to `archive`
        audio_extension = audio_extension[1:]  # remove the dot
        ground_truth_extension = "txt" if is_text_file_available else "srt"

        for ext in [audio_extension, ground_truth_extension]:
            move_file(
                BUCKET,
                f"{job_name}.{ext}",
                f"dropbox/{folder_name}",
                f"archive/{folder_name}",
            )

    # # uncomment this section if we want strict comparison; else, we can simply split based on aligned sections.
    # elif not compare_transcriptions(ground_truth, transcribed_text):
    #     # save Label Studio-ready annotations to `label-studio/raw/{language}/` for further inspection
    #     save_path = f"label-studio/raw/{language}/{folder_name}/{job_name}.json"
    else:
        # otherwise, save annotations to `label-studio/verified` for audio splitting
        save_path = f"label-studio/verified/{folder_name}/{job_name}.json"

    if is_mispronunciation:
        # copy triplets of audio-transcript-ground truth to a separate folder for inspection
        clone_save_prefix = f"mispronunciations/{folder_name}"

        # audio & ground truth
        audio_extension = audio_extension[1:]  # remove the dot
        ground_truth_extension = "txt" if is_text_file_available else "srt"

        for ext in [audio_extension, ground_truth_extension]:
            copy_file(
                BUCKET,
                f"{job_name}.{ext}",
                f"dropbox/{folder_name}",
                clone_save_prefix,
            )

        # transcript
        s3_client.put_object(
            Body=json.dumps(task),
            Bucket=BUCKET,
            Key=f"{clone_save_prefix}/{job_name}.json",
        )

    # export JSON to respective folders in S3
    s3_client.put_object(Body=json.dumps(task), Bucket=BUCKET, Key=save_path)
    print(f"File {save_path} successfully created and saved.")
