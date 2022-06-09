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

from airtable_s3_integration import AirTableS3Integration
from s3_utils import move_file, write_file, delete_file
from typing import Dict, Any, List
import json


class AudioDashboardTable(AirTableS3Integration):
    """
    A class to integrate AudioDashboardTable table and S3. 

    Attributes
    ----------
    airtable_url : str
        URL endpoint to AirTable table.
    filter_formula : str
        Additional GET URL filter formula parameter.
    headers : Dict[str, str]
        API Header containing authorization.
    bucket : str
        S3 bucket name.
    extensions : List[str]
        List of valid file extensions.

    Methods
    -------
    process_table_data() -> None:
        Gets AudioDashboardTable data and applies annotation changes to S3 and finalizes the record.
    _apply_annotation_changes_s3(record: Dict[str, Any]) -> None:
        Applies changes in an S3 directory based on an AirTable `record`'s category verdict.
    _finalize_records(records: List[Dict[str, Any]]) -> None:
        Finalizes audio records by marking "AWS" column as `True`.
    """

    def __init__(self, airtable_url: str, filter_formula: str, headers: Dict[str, str]):
        """Constructor for the `AudioDashboardTable` class.

        Parameters
        ----------
        airtable_url : str
            URL endpoint to AirTable table.
        filter_formula : str
            Additional GET URL filter formula parameter.
        headers : Dict[str, str]
            API Header containing authorization.
        """
        super().__init__(airtable_url, filter_formula, headers)

    def _apply_annotation_changes_s3(self, record: Dict[str, Any]):
        """Applies changes in an S3 directory based on an AirTable `record`'s category verdict.

        Parameters
        ----------
        record : Dict[str, Any]
            An AirTable record/row.
        """
        fields = record["fields"]

        job_name, language = fields["Job Name"], fields["Language"]
        category, transcript = fields["Category"].lower(), fields["Transcript"]
        audio_filename = fields["Audio"][0]["filename"]

        source_path = f"categorisation/raw/{language}"
        save_path = f"categorisation/{category}/{language}"

        if category == "delete":
            delete_file(self.bucket, audio_filename, source_path)
        else:
            move_file(self.bucket, audio_filename, source_path, save_path)
            write_file(self.bucket, transcript, save_path, f"{job_name}.txt")

    def _finalize_records(self, records: List[Dict[str, Any]]):
        """Finalizes audio records by marking "AWS" column as `True`.

        Parameters
        ----------
        records : List[Dict[str, Any]]
            AirTable records.
        """
        payload = json.dumps(
            {
                "records": [
                    {"id": record["id"], "fields": {"AWS": True}} for record in records
                ]
            }
        )
        return payload
