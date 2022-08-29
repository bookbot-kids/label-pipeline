import pytest
import boto3


@pytest.fixture(scope="session")
def transcribe_client():
    return boto3.client("transcribe")
