from airtable_s3_integration import AirTableS3Integration
from typing import Dict, Any, List
from s3_utils import copy_file, delete_file, move_file, bulk_s3_actions
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
    _finalize_record(record: Dict[str, Any]) -> None:
        Finalizes a disfluency record by marking "AWS" column as `True` and updating latest disfluency.
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

        def _get_files_with_extensions(
            job_name: str, extensions: List[str]
        ) -> List[str]:
            return [f"{job_name}.{extension}" for extension in extensions]

        def _lowercase_elements(list_):
            return list(map(lambda x: x.lower(), list_))

        def _get_directories(disfluencies: List[str], language: str) -> List[str]:
            return [
                f"mispronunciations/{disfluency}/{language}"
                for disfluency in disfluencies
            ]

        def _list_difference(list1: List, list2: List) -> List:
            assert len(list1) > len(list2)
            return list(set(list1) - set(list2))

        fields = record["fields"]

        # no changes necessary
        if "Actual Disfluency" not in fields:
            return

        job_name, language = fields["Job Name"], fields["Language"]
        files = _get_files_with_extensions(job_name, self.extensions)

        disfluency = _lowercase_elements(fields["Disfluency"])
        actual_disfluency = _lowercase_elements(fields["Actual Disfluency"])

        sources = _get_directories(disfluency, language)
        targets = _get_directories(actual_disfluency, language)

        if actual_disfluency == ["none"]:  # delete all copies
            bulk_s3_actions(delete_file, self.bucket, files, sources)
        elif len(disfluency) == 1 and len(actual_disfluency) == 1:  # move from A to B
            bulk_s3_actions(move_file, self.bucket, files, sources, targets)
        elif (
            len(disfluency) == 1 and len(actual_disfluency) == 2
        ):  # make additional copy
            actual_disfluency = _list_difference(actual_disfluency, disfluency)
            targets = _get_directories(actual_disfluency, language)
            bulk_s3_actions(copy_file, self.bucket, files, sources, targets)
        elif len(disfluency) == 2 and len(actual_disfluency) == 1:  # delete additional
            disfluency = _list_difference(disfluency, actual_disfluency)
            sources = _get_directories(disfluency, language)
            bulk_s3_actions(delete_file, self.bucket, files, sources)

    def _finalize_record(self, record: Dict[str, Any]):
        """Finalizes a disfluency record by marking "AWS" column as `True`.
        If "Actual Disfluency" is empty (because "Disfluency" is correctly predicted), copy the latter's value to the former.

        Parameters
        ----------
        record : Dict[str, Any]
            An AirTable record.
        """
        fields = {"AWS": True}
        if "Actual Disfluency" not in record["fields"]:
            fields["Actual Disfluency"] = record["fields"]["Disfluency"]

        payload = json.dumps({"records": [{"id": record["id"], "fields": fields}]})
        return payload
