from airtable_s3_integration import AirTableS3Integration
from typing import Dict, Any, List
from s3_utils import delete_file, move_file, write_file
import json


class DisfluencyTable(AirTableS3Integration):
    """
    A class to integrate DisfluencyTable table and S3. 

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
        Gets DisfluencyTable data and applies annotation changes to S3 and finalizes the record.
    _apply_annotation_changes_s3(record: Dict[str, Any]) -> None:
        Applies changes in an S3 directory based on an AirTable `record`'s disfluency verdict.
    _finalize_records(records: List[Dict[str, Any]]) -> None:
        Finalizes disfluency records by marking "AWS" column as `True`.
    """

    def __init__(self, airtable_url: str, filter_formula: str, headers: Dict[str, str]):
        """Constructor for the `DisfluencyTable` class.

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
        """Applies changes in an S3 directory based on an AirTable `record`'s disfluency verdict.

        Parameters
        ----------
        record : Dict[str, Any]
            An AirTable record/row.
        """
        fields = record["fields"]

        job_name, language = fields["Job Name"], fields["Language"]
        disfluency, transcript = fields["Disfluency"].lower(), fields["Transcript"]
        audio_filename = fields["Audio"][0]["filename"]

        source_path = f"mispronunciations/raw/{language}"
        save_path = f"mispronunciations/{disfluency}/{language}"

        if disfluency == "delete":
            delete_file(self.bucket, audio_filename, source_path)
        else:
            move_file(self.bucket, audio_filename, source_path, save_path)
            write_file(self.bucket, transcript, save_path, f"{job_name}.txt")

    def _finalize_records(self, records: List[Dict[str, Any]]):
        """Finalizes disfluency records by marking "AWS" column as `True`.

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
