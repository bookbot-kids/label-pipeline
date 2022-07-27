# Audio Splitter

This library is meant to be used as a bridge between AWS Transcribe and AWS S3, for audio splitting/segmenting/chunking. It takes pairs of audio ground truths and transcriptions, and chunks audio based on their alignment (greedy) annotation. If found, the segments are then exported back to S3.

**Note:** Like other components of this repository, this component is meant to be served as an AWS Lambda Function. However, it can still work if served on any other serverless cloud services. 

## Files

| Component       | Description                                                                                                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lambda Function | Main Lambda Function served on AWS Lambda. Takes in audio alignment annotations, and based on those, segments/splits audios into different files. Audios get exported back to S3. |
| S3 Utils        | Utility library to pull and push files from AWS S3.                                                                                                                               |
| AirTable Logger | Given the alignments and their respective transcripts, export those to AirTable for further optional annotation of audio classification (adult/child) and fix of transcript.      |

## Usage

Since this library is not meant to be used as an API endpoint, it requires a trigger. The trigger we used is whenever a new annotation file arrives at S3, and it runs the main Lambda Function.

## API Reference

Please visit our [documentation](https://bookbot-kids.github.io/label-pipeline/reference/audio_splitter/lambda_function/) page for more details.