from airtable_s3_integration import AirTableS3Integration
from s3_utils import move_file, write_file
from typing import Dict, Any
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
    _finalize_record(record: Dict[str, Any]) -> None:
        Finalizes an audio record by marking "AWS" column as `True`.
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

        move_file(self.bucket, audio_filename, source_path, save_path)
        write_file(self.bucket, transcript, save_path, f"{job_name}.txt")

    def _finalize_record(self, record: Dict[str, Any]):
        """Finalizes an audio record by marking "AWS" column as `True`.

        Parameters
        ----------
        record : Dict[str, Any]
            An AirTable record.
        """
        payload = json.dumps(
            {"records": [{"id": record["id"], "fields": {"AWS": True}}]}
        )
        return payload
