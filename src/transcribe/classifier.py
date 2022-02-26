import requests
import json


class SpeakerClassifier:
    """
    A class to run audio classification.

    Attributes
    ----------
    audio_url : str
        S3 URL pointing to the audio.

    Methods
    -------
    predict() -> str:
        Predicts the audio's speaker type, either child or adult.
    """

    def __init__(self, audio_url: str):
        """Constructor for the `SpeakerClassifier` class.

        Parameters
        ----------
        audio_url : str
            S3 URL pointing to the audio.
        """
        self.audio_url = audio_url
        self.url = "https://ety3wzgylf.execute-api.ap-southeast-1.amazonaws.com/audio-classifier-adult-child"
        self.headers = {"Content-Type": "application/json"}
        self.payload = {"audio_url": self.audio_url}

    def predict(self):
        """Predicts the audio's speaker type, either child or adult.

        Returns
        -------
        str
            "ADULT" or "CHILD", optionally "None" if errs.
        """
        try:
            response = requests.post(
                self.url, headers=self.headers, data=json.dumps(self.payload)
            )
        except Exception as exc:
            print(f"Failed to predict for audio {self.audio_url}")
            print(exc)
            return "None"
        else:
            if response.ok:
                return response.json()["body"]["prediction"]
            else:
                return "None"


if __name__ == "__main__":
    prediction = SpeakerClassifier(
        "s3://bookbot-speech/archive/en-au/8f0ff133-0a55-49e1-ae4f-7be88d429d83_1643700265881.aac"
    ).predict()

    print(prediction)

