import os
import pytest
import boto3
from moto import mock_transcribe


@pytest.fixture
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture()
def transcribe_client(aws_credentials):
    with mock_transcribe():
        conn = boto3.client("transcribe", region_name="ap-southeast-1")
        yield conn