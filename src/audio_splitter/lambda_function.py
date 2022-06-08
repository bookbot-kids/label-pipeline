from typing import Tuple, List, Dict, Any
from urllib.parse import unquote_plus
import os
import json
import ffmpeg
from src.config import ADMIN_EMAIL
from src.audio_splitter.airtable_logger import AirTableLogger
from src.audio_splitter.s3_utils import (
    s3_client,
    move_file,
    get_audio_file,
    create_presigned_url,
)


def trim_audio(input_path: str, start: float, end: float) -> Tuple[bytes, bytes]:
    """Trims audio from `input_path` from `start` to `end` (in seconds), pipes output audio stdout and stderr.
    [Source](https://github.com/kkroening/ffmpeg-python/issues/184#issuecomment-504390452).

    Args:
        input_path (str): Input file URL (`ffmpeg -i` option).
        start (float): Timestamp (in seconds) of the start of the section to keep.
        end (float): Specify time of the first audio sample that will be dropped.

    Returns:
        Tuple[bytes, bytes]: Tuple-pair of stdout and stderr bytes.
    """
    input_stream = ffmpeg.input(input_path)

    aud = input_stream.audio.filter_("atrim", start=start, end=end).filter_(
        "asetpts", "PTS-STARTPTS"
    )

    # # uncomment for aac
    # output = ffmpeg.output(aud, "pipe:", format="adts")

    # kaldi training format: wav, 16bit, 24khz, mono
    # ffmpeg -i in.aac -acodec pcm_s16le -ac 1 -ar 24000 out.wav
    output = ffmpeg.output(
        aud, "pipe:", acodec="pcm_s16le", format="wav", ac=1, ar=24000,
    )
    stdout, stderr = output.run_async(pipe_stdout=True, pipe_stderr=True).communicate()
    return (stdout, stderr)


def split_export_audio(
    annotations: List[Dict[str, Any]],
    annotation_key: str,
    audio_file: str,
    bucket: str,
    key_prefix: str,
) -> None:
    """Splits `audio_file` based on JSON-formatted `annotations`, saves exports to `key_prefix`.

    Args:
        annotations (List[Dict[str, Any]]): _description_
        annotation_key (str): JSON-formatted annotations exported by Label Studio.
        audio_file (str): Key of annotation dictionary containing timestamps and transcriptions.
        bucket (str): Pre-signed URL pointing to the audio file of the JSON annotation.
        key_prefix (str): AWS S3 key prefix path to save file.
    """
    folder_name = os.path.basename(os.path.dirname(audio_file))
    language = folder_name.split("-")[0]

    anno = None

    if annotation_key == "annotations":
        # only get annotations created by admin
        anno = [
            annotation
            for annotation in annotations
            if ADMIN_EMAIL[language] in annotation["created_username"]
        ]
    elif annotation_key == "predictions":
        # otherwise, take correctly predicted transcriptions
        anno = [annotation for annotation in annotations]

    if anno:
        try:
            result = anno[0]["result"]
        except Exception as exc:
            print(exc)

        # only get annotations with start and end times, ignore labels and region-wise GTs
        segments = [
            d
            for d in result
            if "start" in d["value"].keys()
            and "labels" not in d["value"].keys()
            and d["from_name"] != "region-ground-truth"
        ]

        for idx, segment in enumerate(segments):
            save_path = f"training/{key_prefix}-{idx}"
            values = segment["value"]

            try:
                # trim export audio segment
                stdout, stderr = trim_audio(audio_file, values["start"], values["end"])
                s3_client.put_object(Body=stdout, Bucket=bucket, Key=f"{save_path}.wav")

                # export audio segment's transcription
                s3_client.put_object(
                    Body=values["text"][0], Bucket=bucket, Key=f"{save_path}.txt"
                )

                # # TODO: uncomment to enable classifier data collection
                # # export audio segment for categorization
                # s3_client.put_object(
                #     Body=stdout,
                #     Bucket=bucket,
                #     Key=f"categorisation/raw/{key_prefix}-{idx}.wav",
                # )

                # # log to AirTable
                # audio_url = create_presigned_url(bucket, f"{save_path}.wav")

                # logger = AirTableLogger(
                #     os.path.basename(save_path),
                #     audio_url,
                #     values["text"][0],
                #     folder_name,
                # )

                # logger.log_to_airtable()
            except Exception as exc:
                print(f"Error: {exc}")
        print(f"Successfully split and exported to {key_prefix}")
    else:
        print(f"Admin annotation not found")


def lambda_handler(event, context):
    """Event listener for S3 event and calls the split audio function.

    Args:
        event (AWS Event): A JSON-formatted document that contains data for a Lambda function to process.
        context (AWS Event): An object that provides methods and properties that provide information about the invocation, function, and runtime environment.

    Raises:
        e: Audio cannot be obtained from S3.
    """
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")

    job_name = os.path.splitext(os.path.basename(key))[0]
    folder_name = os.path.basename(os.path.dirname(key))

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        task = json.loads(response["Body"].read().decode("utf-8"))
        # "predictions" if immediately correct after Transcribe, else take human "annotations"
        annotation_key = "annotations" if "annotations" in task else "predictions"
        annotations = task[annotation_key]
        # get the corresponding audio file extension
        _, audio_extension = os.path.splitext(os.path.basename(task["data"]["audio"]))
    except Exception as e:
        print(e)
        raise e
    else:
        # get audio file from S3
        audio_file = get_audio_file(bucket, key, audio_extension)
        if audio_file:
            # splits audio + transcription based on annotation, exports to S3
            split_export_audio(
                annotations,
                annotation_key,
                audio_file,
                bucket,
                f"{folder_name}/{job_name}",
            )

            audio_extension = audio_extension[1:]  # removes the dot
            # moves original audio and text to `archive`
            for ext in [audio_extension, "srt", "txt"]:
                move_file(
                    bucket,
                    f"{job_name}.{ext}",
                    f"dropbox/{folder_name}",
                    f"archive/{folder_name}",
                )
