import boto3

s3_client = boto3.client("s3")


def get_audio_file(audio_url: str):
    """Get audio file from AWS S3, in `bucket`.

    Parameters
    ----------
    audio_url : str
        Audio url in S3.

    Returns
    -------
    s3_source_signed_url: str
        Pre-signed URL pointing to the audio file of the JSON annotation.

    Raises
    ------
    exc
        Error fetching file.
    """
    audio_url = audio_url.replace("s3://", "")
    bucket, key = audio_url.split("/", 1)
    try:
        s3_source_signed_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600,
        )
    except Exception as exc:
        print(f"Failed to fetch key: {key}")
        raise exc
    else:
        return s3_source_signed_url
