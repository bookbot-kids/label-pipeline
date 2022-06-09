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

import os
from disfluency_table import DisfluencyTable
from audio_dashboard_table import AudioDashboardTable


def main():
    filter_formula = "filterByFormula=NOT%28%7BAnnotated%7D%20%3D%20%27%27%29"

    headers = {
        "Authorization": f"Bearer {os.environ['AIRTABLE_API_KEY']}",
        "Content-Type": "application/json",
    }

    disfluency_table_url = (
        "https://api.airtable.com/v0/appufoncGJbOg7w4Z/Master?view=Annotated"
    )
    disfluency_table = DisfluencyTable(disfluency_table_url, filter_formula, headers)
    disfluency_table.process_table_data()

    audio_dashboard_table_url = (
        "https://api.airtable.com/v0/appMU2kEdFeVZJ0SS/Master?view=Master"
    )
    audio_dashboard_table = AudioDashboardTable(
        audio_dashboard_table_url, filter_formula, headers
    )
    audio_dashboard_table.process_table_data()

    youtube_audio_dashboard_table_url = (
        "https://api.airtable.com/v0/appZzNIP8ZTitJIiE/Master?view=Master"
    )
    youtube_audio_dashboard_table_url = AudioDashboardTable(
        youtube_audio_dashboard_table_url, filter_formula, headers
    )
    youtube_audio_dashboard_table_url.process_table_data()


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


if __name__ == "__main__":
    main()
