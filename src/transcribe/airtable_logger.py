import os
from typing import Dict, List
import requests
import json
import string


class AirTableLogger:
    """
    A utility class to assist AirTable logging purposes. 
    Contains attributes which holds the audio, ground truth, transcript, and language.

    Attributes
    ----------
    job_name : str
        Job name/id.
    audio_url : str
        URL to audio file.
    ground_truth : str
        Audio text ground truth.
    transcripts : Dict[str, List]
        Resultant output received from AWS Transcribe.
    language : str
        Language of audio.
    category: str
        Type of audio present, defaults to `CHILD` for first log.

    Methods
    -------
    log_to_airtable() -> None:
        Logs results to AirTable.
    """

    def __init__(
        self,
        job_name: str,
        ground_truth: str,
        transcripts: Dict[str, List],
        language: str,
    ):
        """Constructor for the `AirTableLogger` class.

        Parameters
        ----------
        job_name : str
            Job name/id.
        ground_truth : str
            Audio text ground truth.
        transcripts : Dict[str, List]
            Resultant output received from AWS Transcribe.
        language : str
            Language of audio.
        """
        self.job_name = job_name
        self.ground_truth = ground_truth
        self.transcripts = transcripts
        self.language = language
        self.audio_url = None
        self.category = "CHILD"

    def log_to_airtable(self):
        """Logs (`self`) to AirTable.
        """

        def _preprocess_sequence(sequence: str):
            return (
                sequence.replace("-", " ")
                .translate(str.maketrans("", "", string.punctuation))
                .lower()
                .strip()
            )

        def _preprocess_transcripts(transcripts: Dict[str, List]):
            return " ".join(
                [
                    _preprocess_sequence(item["alternatives"][0]["content"])
                    for item in transcripts["items"]
                ]
            )

        fields = {
            "Job Name": self.job_name,
            "Audio": [{"url": self.audio_url}],
            "Language": self.language,
            "Ground Truth": self.ground_truth,
            "Transcript": _preprocess_transcripts(self.transcripts),
            "Category": self.category,
        }

        airtable_url = "https://api.airtable.com/v0/appMU2kEdFeVZJ0SS/Master"
        api_key = os.environ["AIRTABLE_API_KEY"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({"records": [{"fields": fields}]})

        try:
            response = requests.post(airtable_url, headers=headers, data=payload)
        except Exception as exc:
            print(exc)
        else:
            if response.ok:
                print("Successfully logged to AirTable")
            else:
                print("Failed to log to AirTable")
