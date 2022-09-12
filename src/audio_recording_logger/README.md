# Audio Recording Logger

This library is meant to be used to integrate the daily logging results of AWS S3 data inventory and AirTable. It reports audio data recorded, based on their language codes, to AirTable. That way, we can later export this result to an external plotting, e.g. audio recorded over time, and perform further analysis.

**Note:** Like other components of this repository, this component is meant to be served as an AWS Lambda Function. However, it can still work if served on any other serverless cloud services. 

## Files

| Component       | Description                                                                                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lambda Function | Main Lambda Function served on AWS Lambda. Preprocesses dataframe of S3 log files, groups based on training/archive folder and language code, then pushes to AirTable. |
| S3 Utils        | Utility library to pull and push files from AWS S3.                                                                                                                    |
| AirTable Logger | Given filtered and grouped audio log data, export those to AirTable for further analysis.                                                                              |

## Usage

Since this library is not meant to be used as an API endpoint, it requires a trigger. The trigger we used is whenever a new manifest file arrives at S3, and it runs the main Lambda Function.

## API Reference

Please visit our [documentation](https://bookbot-kids.github.io/label-pipeline/reference/audio_recording_logger/lambda_function/) page for more details.