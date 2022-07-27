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

from typing import Dict, Any, List
import requests
from config import BUCKET, EXTENSIONS


class AirTableS3Integration:
    def __init__(self, airtable_url: str, filter_formula: str, headers: Dict[str, str]):
        """Constructor for the `AirTableS3Integration` class.

        Args:
            airtable_url (str): URL endpoint to AirTable table.
            filter_formula (str): Additional GET URL filter formula parameter.
            headers (Dict[str, str]): API Header containing authorization.
        """
        self.airtable_url = airtable_url
        self.filter_formula = filter_formula
        self.headers = headers
        self.bucket = BUCKET
        self.extensions = EXTENSIONS

    def process_table_data(self):
        """Gets AirTable data and applies annotation changes to S3 and finalizes the record."""
        records, offset = [], 0
        while True:
            try:
                response = requests.get(
                    f"{self.airtable_url}&{self.filter_formula}",
                    params={"offset": offset},
                    headers=self.headers,
                )
            except Exception as exc:
                print(exc)
            else:
                if response.ok:
                    response = response.json()
                    records += response["records"]

                    if "offset" in response:
                        offset = response["offset"]
                    else:
                        break
                else:
                    print("Failed to get data from AirTable")

        # batch size: 10
        for i in range(0, len(records), 10):
            batch = records[i : i + 10]
            for record in batch:
                self._apply_annotation_changes_s3(record)
            self._patch_record(self._finalize_records(batch))

    def _patch_record(self, payload: str):
        """Patches `payload` to `self.airtable_url` with authorized `self.headers`.

        Args:
            payload (str): Record payload.
        """
        try:
            response = requests.patch(
                self.airtable_url, headers=self.headers, data=payload
            )
        except Exception as exc:
            print(exc)
        else:
            if response.ok:
                return
            else:
                print(f"Failed to patch {payload}")

    def _apply_annotation_changes_s3(self, record: Dict[str, Any]):
        """Applies changes in an S3 directory based on an AirTable `record`'s annotation verdict.

        Args:
            record (Dict[str, Any]): An AirTable record/row.
        """
        pass

    def _finalize_records(self, records: List[Dict[str, Any]]) -> str:
        """Finalizes records by marking "AWS" column as `True`.

        Args:
            records (List[Dict[str, Any]]): AirTable records.

        Returns:
            str: Finalized record payload.
        """
        pass
