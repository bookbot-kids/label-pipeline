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

from datetime import datetime, date
import pandas as pd
from urllib.parse import unquote_plus
from math import ceil
import json
import io

from s3_utils import S3Client
from airtable import AirTable

AUDIO_EXTENSIONS = ["wav", "aac", "m4a"]

s3_client = S3Client(region_name="ap-southeast-1")


def get_log_files(bucket: str, manifest_file_path: str) -> pd.DataFrame:
    """Gets all log files as listed in S3 inventory manifest file.

    Args:
        bucket (str): AWS S3 manifest file's bucket name.
        manifest_file_path (str): AWS S3 path to manifest file.

    Returns:
        pd.DataFrame: DataFrame of all log files, concatenated.
    """
    manifest_file = s3_client.get_object(bucket, manifest_file_path)
    files = json.loads(manifest_file)["files"]
    file_keys = [file["key"] for file in files]
    dfs = []
    for key in file_keys:
        log_file = s3_client.get_object(bucket, key)
        log_file_df = pd.read_csv(io.BytesIO(log_file), compression="gzip", header=None)
        dfs.append(log_file_df)
    return pd.concat(dfs)


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Perform basic preprocessing on concatenated S3 inventory log files.

    - Rename columns to `bucket`, `key`, `size`, and `last_modified_date`.
    - Converts `date` column to `datetime` type.
    - Gets language code of item based on `key`, e.g. `en-AU`.
    - Gets language of item based on `language`, e.g. `en`.
    - Gets folder name of item based on `key`, e.g. `training`, `archive`.
    - Gets filename suffix based on `key`, e.g. `aac`, `wav`.
    - Only filters for audio files based on extensions found in `AUDIO_EXTENSIONS`.

    Args:
        df (pd.DataFrame): DataFrame of all log files, concatenated.

    Returns:
        pd.DataFrame: Preprocessed DataFrame based on the outline above.
    """
    df.columns = ["bucket", "key", "size", "last_modified_date"]
    df["date"] = pd.to_datetime(df["last_modified_date"]).dt.date
    df["language-code"] = df["key"].apply(lambda key: key.split("/")[-2])
    df["language"] = df["language-code"].apply(lambda x: x.split("-")[0])
    df["folder"] = df["key"].apply(lambda key: key.split("/")[0])
    df["suffix"] = df["key"].apply(lambda key: key.split("/")[-1].split(".")[-1])
    df = df[df["suffix"].apply(lambda x: x in AUDIO_EXTENSIONS)]
    return df


def groupby_language_total_bytes(df: pd.DataFrame, folder: str) -> pd.DataFrame:
    """Filters DataFrame by folder, then groups by:

    - `date`,
    - `folder`,
    - `language`,
    - `language-code`,

    then sums the duration of each group.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame to group.
        folder (str): Name of folder to filter for.

    Returns:
        pd.DataFrame: Filtered and grouped-by DataFrame.
    """
    filtered_df = df[df["folder"] == folder]
    return pd.DataFrame(
        filtered_df.groupby(["date", "folder", "language", "language-code"])[
            "size"
        ].agg("sum")
    ).reset_index()


def calculate_audio_duration(
    size_bytes: int,
    sample_rate: int,
    bit_depth: int = None,
    bit_rate: int = None,
    num_channels: int = 1,
) -> int:
    """Calculates audio duration based on audio file metadata.

    Args:
        size_bytes (int): Size of file in bytes.
        sample_rate (int): Sample rate of audio.
        bit_depth (int, optional): Bit depth of audio, e.g. 16. Defaults to None.
        bit_rate (int, optional): Bit rate of audio if compressed, e.g. 95kbps. Defaults to None.
        num_channels (int, optional): Number of channels in audio. Defaults to 1 (mono).

    Returns:
        int: Estimated audio duration, in seconds.
    """
    if not bit_rate:
        bit_rate = bit_depth * sample_rate
    bits = size_bytes * 8
    duration = bits / (bit_rate * num_channels)
    return ceil(duration)


def lambda_handler(event, context):
    """Event listener for S3 event and calls the daily logger function.

    Args:
        event (AWS Event):
            A JSON-formatted document that contains data for a Lambda function to process.
        context (AWS Context):
            An object that provides methods and properties that provide information about the invocation, function, and runtime environment.
    """
    # manifest.json file
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    manifest_file_path = unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    manifest_file_date = manifest_file_path.split("/")[-2].replace("T01-00Z", "")
    query_date = datetime.strptime(manifest_file_date, "%Y-%m-%d").date()
    main(bucket, manifest_file_path, query_date)


def main(bucket: str, manifest_file_path: str, query_date: datetime.date) -> None:
    """Main function to be executed by `lambda_handler`.

    - Gets all log files from manifest file, then preprocesses it.
    - Gets all audio in `training` and `archive` folder.
        - Groups audios based on language code.
        - Calculates total audio duration for each language code.
        - Converts `date` column to string for AirTable upload purposes.
        - Drops unused `size` column.
    - Push both resultant DataFrames to AirTable.

    Args:
        bucket (str): AWS S3 manifest file's bucket name.
        manifest_file_path (str): AWS S3 path to manifest file.
        query_date (datetime.date): Query date to filter with.
    """
    # get all files, create dataframe, apply preprocessing
    df = preprocess_dataframe(get_log_files(bucket, manifest_file_path))
    # filter by date
    df = df[df["date"] == query_date]

    # training dataframe
    training = groupby_language_total_bytes(df, "training")
    training["duration"] = training["size"].apply(
        lambda x: calculate_audio_duration(x, sample_rate=24000, bit_depth=16)
    )
    training["date"] = training["date"].apply(str)
    training = training.drop(labels=["size"], axis=1)

    # archive dataframe
    archive = groupby_language_total_bytes(df, "archive")
    archive["duration"] = archive["size"].apply(
        lambda x: calculate_audio_duration(x, sample_rate=16000, bit_rate=95000)
    )
    archive["date"] = archive["date"].apply(str)
    archive = archive.drop(labels=["size"], axis=1)

    airtable = AirTable("https://api.airtable.com/v0/app1j9JeeX1jXegnL/Master")

    airtable.batch_add_records(
        [{"fields": d} for d in archive.to_dict(orient="records")]
    )
    airtable.batch_add_records(
        [{"fields": d} for d in training.to_dict(orient="records")]
    )
