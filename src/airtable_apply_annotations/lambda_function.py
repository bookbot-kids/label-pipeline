import json
import os
from typing import Any, Callable, Dict, List
import requests
import boto3
from botocore.exceptions import ClientError
from config import BUCKET, EXTENSIONS

s3_resource = boto3.resource("s3")


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
    try:
        s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
            CopySource=f"{bucket}/{source}/{file}"
        )
        print(
            f"Copied file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
    except ClientError as exc:
        return


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
    try:
        s3_resource.Object(bucket, f"{destination}/{file}").copy_from(
            CopySource=f"{bucket}/{source}/{file}"
        )
        s3_resource.Object(bucket, f"{source}/{file}").delete()
        print(
            f"Moved file from {bucket}/{source}/{file} to {bucket}/{destination}/{file}"
        )
    except ClientError as exc:
        return


def delete_file(bucket, file, source):
    """Delete `file` in `bucket` from `source` folder

    Parameters
    ----------
    bucket : str
        S3 bucket name.
    file : str
        Name of file to be deleted (without full-path).
    source : str
        Source folder in S3 bucket.
    """
    try:
        s3_resource.Object(bucket, f"{source}/{file}").delete()
        print(f"Deleted file from {bucket}/{source}/{file}")
    except ClientError as exc:
        return


def bulk_s3_actions(
    action: Callable,
    bucket: str,
    files: List[str],
    sources: List[str],
    targets: List[str] = None,
):
    """Applies a bulk S3 CRUD action for all `files` in `sources` and optionally, `targets`.

    Parameters
    ----------
    action : Callable
        Function calling an S3 CRUD operation.
    bucket : str
        S3 bucket name.
    files : List[str]
        List of files in `bucket`/`sources`
    sources : List[str]
        Source folders in `bucket`.
    targets : List[str], optional
        Target folders in `bucket`, by default None
    """
    if targets:
        assert len(sources) == len(targets)
        for source, target in zip(sources, targets):
            for file in files:
                action(bucket=bucket, file=file, source=source, destination=target)
    else:
        for source in sources:
            for file in files:
                action(bucket=bucket, file=file, source=source)


def finalize_record(record: Dict[str, Any], airtable_url: str, headers: Dict[str, str]):
    """Finalizes a record by marking "AWS" column as `True`.
    If "Actual Disfluency" is empty (because "Disfluency" is correctly predicted), copy the latter's value to the former.

    Parameters
    ----------
    record : Dict[str, Any]
        An AirTable record.
    airtable_url : str
        AirTable Table endpoint URL.
    headers : Dict[str, str]
        Headers for PATCH request, containing API key.
    """
    fields = {"AWS": True}
    if "Actual Disfluency" not in record["fields"]:
        fields["Actual Disfluency"] = record["fields"]["Disfluency"]

    payload = json.dumps({"records": [{"id": record["id"], "fields": fields}]})
    try:
        response = requests.patch(airtable_url, headers=headers, data=payload)
    except Exception as exc:
        print(exc)
    else:
        if response.ok:
            print("Successfully patched to AirTable")
        else:
            print("Failed to patch to AirTable")


def apply_annotation_changes_s3(record: Dict[str, Any]):
    """Applies changes in an S3 directory based on an AirTable `record`'s annotation verdict.

    Parameters
    ----------
    record : Dict[str, Any]
        An AirTable record/row.

    Examples
    -----------------------------------------------------
    | Disfluency | Actual Disfluency |      Verdict     |
    |:----------:|:-----------------:|:----------------:|
    |      Σ     |         -         |    Do Nothing    |
    |      Σ     |        None       |   Delete from Σ  |
    |      A     |         B         | Move from A to B |
    |      A     |        A, B       | Copy from A to B |
    |    A, B    |         A         |   Delete from B  |
    -----------------------------------------------------
    """

    def _get_files_with_extensions(job_name: str, extensions: List[str]) -> List[str]:
        return [f"{job_name}.{extension}" for extension in extensions]

    def _lowercase_elements(list_):
        return list(map(lambda x: x.lower(), list_))

    def _get_directories(disfluencies: List[str], language: str) -> List[str]:
        return [
            f"mispronunciations/{disfluency}/{language}" for disfluency in disfluencies
        ]

    def _list_difference(list1: List, list2: List) -> List:
        assert len(list1) > len(list2)
        return list(set(list1) - set(list2))

    fields = record["fields"]

    # no changes necessary
    if "Actual Disfluency" not in fields:
        return

    job_name, language = fields["Job Name"], fields["Language"]
    files = _get_files_with_extensions(job_name, EXTENSIONS)

    disfluency = _lowercase_elements(fields["Disfluency"])
    actual_disfluency = _lowercase_elements(fields["Actual Disfluency"])

    sources = _get_directories(disfluency, language)
    targets = _get_directories(actual_disfluency, language)

    if actual_disfluency == ["none"]:  # delete all copies
        bulk_s3_actions(delete_file, BUCKET, files, sources)
    elif len(disfluency) == 1 and len(actual_disfluency) == 1:  # move from A to B
        bulk_s3_actions(move_file, BUCKET, files, sources, targets)
    elif len(disfluency) == 1 and len(actual_disfluency) == 2:  # make additional copy
        actual_disfluency = _list_difference(actual_disfluency, disfluency)
        targets = _get_directories(actual_disfluency, language)
        bulk_s3_actions(copy_file, BUCKET, files, sources, targets)
    elif len(disfluency) == 2 and len(actual_disfluency) == 1:  # delete additional
        disfluency = _list_difference(disfluency, actual_disfluency)
        sources = _get_directories(disfluency, language)
        bulk_s3_actions(delete_file, BUCKET, files, sources)


def main():
    # SELECT * FROM Master WHERE Annotated != ""
    # NOT({Annotated} = "") in AirScript, i.e., where it has been annotated by labeler
    # AWS filter (changes finalized) is automatically applied to the cURL request as it is filtered in AirTable through view
    filter_formula = "filterByFormula=NOT%28%7BAnnotated%7D%20%3D%20%27%27%29"
    airtable_url = "https://api.airtable.com/v0/appufoncGJbOg7w4Z/Master?view=Master"

    api_key = os.environ["AIRTABLE_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(f"{airtable_url}&{filter_formula}", headers=headers)
    except Exception as exc:
        print(exc)
    else:
        if response.ok:
            records = response.json()["records"]
            for record in records:
                apply_annotation_changes_s3(record)
                finalize_record(record, airtable_url, headers)
        else:
            print("Failed to get data from AirTable")


def lambda_handler(event, context):
    """Event listener for S3 event and calls the daily logger function.

    Parameters
    ----------
    event : AWS Event
        A JSON-formatted document that contains data for a Lambda function to process.
    context : AWS Context
        An object that provides methods and properties that provide information about the invocation, function, and runtime environment.
    """
    main()
