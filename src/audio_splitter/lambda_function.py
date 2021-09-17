import boto3
from urllib.parse import unquote_plus
import os
import json
import ffmpeg
from config import ADMIN_EMAIL, SIGNED_URL_TIMEOUT

s3_client = boto3.client("s3")


def get_audio_file(bucket, key):
    """Get corresponding audio file of JSON annotation (`key`) from AWS S3, in `bucket`.

    Parameters
    ----------
    bucket : str
        Audio and JSON bucket name in S3.
    key : str
        JSON file key name in S3.

    Returns
    -------
    s3_source_signed_url: str
        Pre-signed URL pointing to the audio file of the JSON annotation.
    """
    job_name = os.path.splitext(os.path.basename(key))[0]
    folder_name = os.path.basename(os.path.dirname(key))
    audio_file = f"dropbox/{folder_name}/{job_name}.aac"
    try:
        s3_source_signed_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": audio_file},
            ExpiresIn=SIGNED_URL_TIMEOUT,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        print(f"Failed to fetch key: {audio_file}")
    else:
        print(f"Successfully fetched {audio_file}")
        return s3_source_signed_url


def trim_audio(input_path, start, end):
    """Trims audio from `input_path` from `start` to `end` (in seconds), pipes output audio stdout and stderr.
    Source: https://github.com/kkroening/ffmpeg-python/issues/184#issuecomment-504390452

    Parameters
    ----------
    input_path : str
        Input file URL (ffmpeg -i option).
    start : float
        Timestamp (in seconds) of the start of the section to keep.
    end : float
        Specify time of the first audio sample that will be dropped.

    Returns
    -------
    Tuple[bytes, bytes]
        Tuple-pair of stdout and stderr bytes.
    """

    input_stream = ffmpeg.input(input_path)

    aud = input_stream.audio.filter_("atrim", start=start, end=end).filter_(
        "asetpts", "PTS-STARTPTS"
    )

    output = ffmpeg.output(aud, "pipe:", format="adts")
    stdout, stderr = output.run_async(pipe_stdout=True, pipe_stderr=True).communicate()
    return (stdout, stderr)


def split_export_audio(annotations, audio_file, bucket, key_prefix):
    """Splits `audio_file` based on JSON-formatted `annotations`, saves exports to `key_prefix`.

    Parameters
    ----------
    annotations : List[Dict[str, Any]]
        JSON-formatted annotations exported by Label Studio.
    audio_file : str
        Pre-signed URL pointing to the audio file of the JSON annotation.
    key_prefix : str
        AWS S3 key prefix path to save file.
    """
    language = os.path.basename(os.path.dirname(audio_file)).split("-")[0]

    admin_annotation = [
        annotation
        for annotation in annotations
        if ADMIN_EMAIL[language] in annotation["created_username"]
    ]

    if admin_annotation:
        try:
            result = admin_annotation[0]["result"]
        except Exception as exc:
            print(exc)

        # only get annotations with start and end times, ignore labels
        segments = [
            d
            for d in result
            if "start" in d["value"].keys() and "labels" not in d["value"].keys()
        ]

        for idx, segment in enumerate(segments):
            save_path = f"training/{key_prefix}-{idx}"
            values = segment["value"]

            try:
                # trim export audio segment
                stdout, stderr = trim_audio(audio_file, values["start"], values["end"])
                s3_client.put_object(Body=stdout, Bucket=bucket, Key=f"{save_path}.aac")

                # export audio segment's transcription
                s3_client.put_object(
                    Body=values["text"][0], Bucket=bucket, Key=f"{save_path}.txt"
                )
            except Exception as exc:
                print(f"Error: {exc}")
        print(f"Successfully split and exported to {key_prefix}")
    else:
        print(f"Admin annotation not found")


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
    """Event listener for S3 event and calls the split audio function.

    Parameters
    ----------
    event : AWS Event
        A JSON-formatted document that contains data for a Lambda function to process.
    context : AWS Context
        An object that provides methods and properties that provide information about the invocation, function, and runtime environment.
    """
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")

    job_name = os.path.splitext(os.path.basename(key))[0]
    folder_name = os.path.basename(os.path.dirname(key))

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        task = json.loads(response["Body"].read().decode("utf-8"))
        annotations = task["annotations"]
    except Exception as e:
        print(e)
        raise e
    else:
        # get audio file from S3
        audio_file = get_audio_file(bucket, key)
        # splits audio + transcription based on annotation, exports to S3
        split_export_audio(annotations, audio_file, bucket, f"{folder_name}/{job_name}")

        # moves original audio and text to `archive`
        for ext in ["aac", "txt"]:
            move_file(
                bucket,
                f"{job_name}.{ext}",
                f"dropbox/{folder_name}",
                f"archive/{folder_name}",
            )
