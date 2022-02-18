import requests
import json

url = "https://ety3wzgylf.execute-api.ap-southeast-1.amazonaws.com/audio-classifier-adult-child"

headers = {"Content-Type": "application/json"}

payload = {
    "audio_url": "s3://bookbot-speech/archive/en-au/8f0ff133-0a55-49e1-ae4f-7be88d429d83_1643700265881.aac"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(response.json())

