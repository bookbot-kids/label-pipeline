import pytest
from src.transcribe.s3_utils import S3Client
from src.transcribe.transcribe import TranscribeStatus, TranscribeClient
from src.transcribe.lambda_function import get_language_code, get_ground_truth


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


def test_lambda_function(s3_client, s3_test, transcribe_client, transcribe_test):
    assert get_language_code("s3://bucket/folder/en-au/filename.aac") == "en-AU"
    assert get_ground_truth("folder/filename.txt") == (None, None)
