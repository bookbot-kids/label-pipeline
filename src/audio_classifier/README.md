# Audio Classifier

An audio classifier API function, distinguishing between adult and child voice/speech. We used audio classifier models which we have released as open-source models in [HuggingFace](https://huggingface.co/bookbot). The audios have to live in AWS S3, which is then pulled and passed for inference to the classifier model.

**Note:** Like other components of this repository, this component is meant to be served as an AWS Lambda Function. However, it can still work if served on any other serverless cloud services. 

## Files

| Component       | Description                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Lambda Function | Main Lambda Function served on AWS Lambda. Has authorization integrated and requires ONNX-ready audio classifier model to work. |
| S3 Utils        | Utility library to pull audios from AWS S3.                                                                                     |

## Usage

The API expects the following request body.

```py
payload = {
    "audio_url": "s3://BUCKET/AUDIO_KEY"
}
event = {"body": json.dumps(payload)}
response = lambda_handler(event, None)
print(response)
```

## API Reference

Please visit our [documentation](https://bookbot-kids.github.io/label-pipeline/reference/audio_classifier/lambda_function/) page for more details.