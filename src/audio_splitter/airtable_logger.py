import os
import requests
import json


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
    transcripts : str
        Transcription received from AWS Transcribe.
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
        self, job_name: str, audio_url: str, transcript: str, language: str,
    ):
        """Constructor for the `AirTableLogger` class.

        Parameters
        ----------
        job_name : str
            Job name/id.
        audio_url : str
            URL to audio file.
        transcripts : str
            Transcription received from AWS Transcribe.
        language : str
            Language of audio.
        """
        self.job_name = job_name
        self.audio_url = audio_url
        self.transcript = transcript
        self.language = language
        self.category = "CHILD"

    def log_to_airtable(self):
        """Logs `self` to AirTable.
        """
        fields = {
            "Job Name": self.job_name,
            "Audio": [{"url": self.audio_url}],
            "Language": self.language,
            "Transcript": self.transcript,
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
