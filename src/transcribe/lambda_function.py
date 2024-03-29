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

import os
import string
from typing import Dict, List, Tuple
from urllib.parse import unquote_plus

from src.config import BUCKET, SIGNED_URL_TIMEOUT, LANGUAGE_CODES
from src.transcribe.homophones import HOMOPHONES
from src.transcribe.mispronunciation import detect_mispronunciation, Mispronunciation
from src.transcribe.srt2txt import srt2txt
from src.transcribe.classifier import SpeakerClassifier
from src.transcribe.transcribe import TranscribeClient, TranscribeStatus
from src.transcribe.s3_utils import S3Client
from src.transcribe.aligner import overlapping_segments

s3_client = S3Client(region_name="ap-southeast-1")
transcribe_client = TranscribeClient(region_name="ap-southeast-1")


def get_language_code(filename: str) -> str:
    """Get language code from filename for transcribing

    Args:
        filename (str): Audio filename with complete S3 path.

    Returns:
        str: Language code of the audio file, formatted for AWS Transcribe.
    """
    folder = os.path.basename(os.path.dirname(filename))
    language, country = folder.split("-")
    language_code = f"{language}-{country.upper()}"

    if language_code not in LANGUAGE_CODES:
        # defaults to US English and ID Indonesian if not supported
        return "en-US" if language == "en" else "id-ID"

    return language_code


def get_ground_truth(ground_truth_filename_prefix: str) -> Tuple[str, str]:
    """Attempts to grab ground truth file from S3, either ending in txt or srt.

    Args:
        ground_truth_filename_prefix (str): Prefix of ground truth file name.

    Returns:
        Tuple[str, str]: Pair of [ground truth string, ground truth file extension],
            otherwise `[None, None]`.
    """
    txt_transcript_file = s3_client.get_object(
        BUCKET, f"{ground_truth_filename_prefix}.txt"
    )
    srt_transcript_file = s3_client.get_object(
        BUCKET, f"{ground_truth_filename_prefix}.srt"
    )

    # if txt exists
    if txt_transcript_file:
        return (txt_transcript_file["Body"].read().decode("utf-8"), "txt")
    elif srt_transcript_file:
        return (srt2txt(srt_transcript_file["Body"].read().decode("utf-8")), "srt")
    else:
        return (None, None)


def classify_mispronunciation(
    results: Dict[str, List], ground_truth: str, language: str
) -> Mispronunciation:
    """Classifies if a transcription result and ground truth text is a case of
    mispronunciation.

    Args:
        results (Dict[str, List]): Resultant output received from AWS Transcribe.
        ground_truth (str): Ground truth text for the corresponding annotation.
        language (str): Language of the transcript-ground truth pair.

    Returns:
        Mispronunciation: Object of mispronunciation present.
    """

    def _preprocess_sequence(sequence):
        return (
            sequence.replace("-", " ")
            .translate(str.maketrans("", "", string.punctuation))
            .lower()
            .strip()
        )

    transcripts = [
        _preprocess_sequence(item["alternatives"][0]["content"])
        for item in results["items"]
    ]

    ground_truth = _preprocess_sequence(ground_truth).split()

    homophones = HOMOPHONES[language] if language in HOMOPHONES else None

    mispronunciation = detect_mispronunciation(ground_truth, transcripts, homophones)

    return mispronunciation


def lambda_handler(event, context):
    """Event listener for S3 event and calls Transcribe job.

    Args:
        event (AWS Event):
            A JSON-formatted document that contains data for a Lambda function
            to process.
        context (AWS Context):
            An object that provides methods and properties that provide information
            about the invocation, function, and runtime environment.
    """
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    main(f"s3://{bucket}/{key}")


def main(audio_file: str):
    """Main function to run Transcribe, generate Label Studio JSON-annotation,
    and saves JSON to S3.

    Args:
        audio_file (str): Audio filename with complete S3 path.
    """
    EXT2FORMAT = {"wav": "wav", "m4a": "mp4", "aac": "mp4"}
    job_name, audio_extension = os.path.splitext(os.path.basename(audio_file))
    audio_extension = audio_extension[1:]
    folder_name = os.path.basename(os.path.dirname(audio_file))
    language = folder_name.split("-")[0]
    language_code = get_language_code(audio_file)
    ground_truth, ground_truth_ext = get_ground_truth(
        f"dropbox/{folder_name}/{job_name}"
    )

    speaker_type = SpeakerClassifier(audio_file).predict()
    if speaker_type == "ADULT":
        print("Adult audio detected. Archiving audio.")
        for ext in [audio_extension, ground_truth_ext]:
            s3_client.move_file(
                BUCKET,
                f"{job_name}.{ext}",
                f"dropbox/{folder_name}",
                f"archive/adult/{folder_name}",
            )
        return

    status, results, task = transcribe_client.transcribe_file(
        job_name,
        audio_file,
        media_format=EXT2FORMAT[audio_extension],
        language_code=language_code,
    )

    transcribed_text = task["predictions"][0]["result"][0]["value"]["text"][0]
    mispronunciation = None

    if status == TranscribeStatus.SUCCESS:
        if ground_truth is not None:
            # classify for mispronunciation
            mispronunciation = classify_mispronunciation(
                results, ground_truth, language
            )
            # add ground truth to Label Studio JSON-annotated task (for reference)
            task["data"]["text"] = ground_truth
            # add region-wise transcriptions and ground truth (for convenience
            # of labeler)
            task["predictions"][0]["result"] += overlapping_segments(
                results, ground_truth, language, max_repeats=3
            )

    if status == TranscribeStatus.FAILED or transcribed_text == "":
        # archive Transcribe-failed annotations
        save_path = f"archive/{folder_name}/{job_name}.json"
        # move audios to `archive`
        for ext in [audio_extension, ground_truth_ext]:
            s3_client.move_file(
                BUCKET,
                f"{job_name}.{ext}",
                f"dropbox/{folder_name}",
                f"archive/{folder_name}",
            )
    else:
        # otherwise, save annotations to `label-studio/verified` for audio splitting
        save_path = f"label-studio/verified/{folder_name}/{job_name}.json"

    if mispronunciation:
        # copy audio to a separate folder for annotation
        s3_client.copy_file(
            BUCKET,
            f"{job_name}.{audio_extension}",
            f"dropbox/{folder_name}",
            f"mispronunciations/raw/{folder_name}",
        )

        # log results to AirTable
        mispronunciation.job_name = job_name
        mispronunciation.language = folder_name
        mispronunciation.audio_url = s3_client.create_presigned_url(
            BUCKET,
            f"mispronunciations/raw/{folder_name}/{job_name}.{audio_extension}",
            SIGNED_URL_TIMEOUT,
        )

    # export JSON to respective folders in S3
    s3_client.put_object(task, BUCKET, save_path)
    print(f"File {save_path} successfully created and saved.")
