import pytest
from src.transcribe.s3_utils import S3Client
from src.transcribe.transcribe import TranscribeStatus, TranscribeClient
from src.transcribe.mispronunciation import Mispronunciation, MispronunciationType


@pytest.fixture
def bucket_name():
    return "my-test-bucket"


@pytest.fixture
def s3_test(s3_client, bucket_name):
    s3_client.create_bucket(Bucket=bucket_name)
    yield


@pytest.fixture
def transcribe_test(transcribe_client):
    job_name = "MyJob"
    args = {
        "TranscriptionJobName": job_name,
        "Media": {"MediaFileUri": "s3://my-test-bucket/my-media-file.wav"},
        "MediaFormat": "wav",
        "LanguageCode": "en-US",
    }
    resp = transcribe_client.start_transcription_job(**args)
    resp["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_transcribe(transcribe_client, transcribe_test):
    file_name = "s3://my-test-bucket/file.wav"
    success_task = (
        TranscribeStatus.FAILED,
        None,
        {
            "data": {"audio": "s3://my-test-bucket/file.wav"},
            "predictions": [
                {
                    "model_version": "amazon_transcribe",
                    "result": [
                        {
                            "from_name": "transcription",
                            "to_name": "audio",
                            "type": "textarea",
                            "value": {"text": [""]},
                        }
                    ],
                }
            ],
        },
    )
    failed_task = (
        TranscribeStatus.FAILED,
        None,
        {
            "data": {"audio": file_name},
            "predictions": [
                {
                    "model_version": "amazon_transcribe",
                    "result": [
                        {
                            "from_name": "transcription",
                            "to_name": "audio",
                            "type": "textarea",
                            "value": {"text": [""]},
                        },
                    ],
                }
            ],
        },
    )
    job = {"TranscriptionJob": {"Transcript": {"TranscriptFileUri": file_name}}}
    my_client = TranscribeClient()

    assert my_client.get_job(transcribe_client, "MyJob") is not None
    assert my_client.create_task(file_name, job) == failed_task
    assert my_client.create_task(file_name, {}) == failed_task
    assert my_client.transcribe_file("MyJob", file_name) == success_task
    assert my_client.transcribe_file("NewJob", file_name) == failed_task


def test_s3_utils(s3_client, s3_test):
    my_client = S3Client()
    my_client.put_object('{"data": "hello"}', "my-test-bucket", "source/test_file")
    my_client.copy_file("my-test-bucket", "test_file", "source", "dest")
    my_client.move_file("my-test-bucket", "test_file", "source", "dest")
    assert my_client.get_object("my-test-bucket", "dest/test_file") is not None
    assert my_client.create_presigned_url("my-test-bucket", "test_file").startswith(
        "https://my-test-bucket.s3.amazonaws.com/test_file"
    )


def test_lambda_function(
    s3_client, s3_test, transcribe_client, transcribe_test, intialize_credentials
):
    from src.transcribe.lambda_function import (
        get_language_code,
        get_ground_truth,
        classify_mispronunciation,
        lambda_handler,
    )

    results = {
        "items": [
            {
                "start_time": "6.69",
                "end_time": "6.88",
                "alternatives": [{"confidence": "1.0", "content": "Saya"}],
                "type": "pronunciation",
            },
            {
                "start_time": "6.88",
                "end_time": "7.17",
                "alternatives": [{"confidence": "0.9461", "content": "enggak"}],
                "type": "pronunciation",
            },
            {
                "start_time": "7.17",
                "end_time": "7.27",
                "alternatives": [{"confidence": "0.9461", "content": "tahu"}],
                "type": "pronunciation",
            },
        ],
    }
    mispronunciation = Mispronunciation(
        MispronunciationType.SUBSTITUTION,
        (["saya", "enggak", "mau"], ["saya", "enggak", "tahu"]),
        (["mau"], ["tahu"]),
        [("equal", 0, 2, 0, 2), ("replace", 2, 3, 2, 3)],
    )
    output = classify_mispronunciation(results, "saya enggak mau", "id")

    test_event = {
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {"principalId": "EXAMPLE"},
                "requestParameters": {"sourceIPAddress": "127.0.0.1"},
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/abcdef/mnopqrstuvwxyzABCDEFGH",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": "my-test-bucket",
                        "ownerIdentity": {"principalId": "EXAMPLE"},
                        "arn": "arn:aws:s3:::my-test-bucket",
                    },
                    "object": {
                        "key": "folder/id-id/MyJob.wav",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901",
                    },
                },
            }
        ]
    }

    assert get_language_code("s3://bucket/folder/en-au/filename.aac") == "en-AU"
    assert get_language_code("s3://bucket/folder/id-US/filename.aac") == "id-ID"
    assert get_ground_truth("transcript") == (None, None)
    assert vars(output) == vars(mispronunciation)
    assert lambda_handler(test_event, None) is None
