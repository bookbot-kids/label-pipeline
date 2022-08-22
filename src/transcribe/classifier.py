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

import requests
import json
import os


class SpeakerClassifier:
    """
    A class to run audio classification.

    Attributes:
        audio_url (str): S3 URL pointing to the audio.
    """

    def __init__(self, audio_url: str):
        """Constructor for the `SpeakerClassifier` class.

        Args:
            audio_url (str): S3 URL pointing to the audio.
        """
        self.audio_url = audio_url
        api = "audio-classifier-adult-child"
        self.url = f"https://ety3wzgylf.execute-api.ap-southeast-1.amazonaws.com/{api}"
        self.headers = {
            "Authorization": os.environ["API_KEY"],
            "Content-Type": "application/json",
        }
        self.payload = {"audio_url": self.audio_url}

    def predict(self) -> str:
        """Predicts the audio's speaker type, either child or adult.

        Returns:
            str: "ADULT" or "CHILD", optionally "None" if errs.
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
    test_audio = "386cc312-5a30-41a6-a21b-c2184c225260_1636982327979"
    prediction = SpeakerClassifier(
        f"s3://bookbot-speech/archive/id-id/{test_audio}.aac"
    ).predict()

    print(prediction)
