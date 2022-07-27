# AirTable Apply Annotations

This library integrates annotation done in AirTable and performs file changes in AWS S3. This library is aims to only be used for internal labeling purposes, hence changes are needed if it were to be integrated based on your own requirements. The main feature of this library is to create an API to interface with various AirTable tables and make changes dedicated to each of those tables. 

In our case, we had three main annotations:
- Transcription Fixes
- Mispronunciation Type
- Adult/Child Speech Classification

**Note:** Like other components of this repository, this component is meant to be served as an AWS Lambda Function. However, it can still work if served on any other serverless cloud services. 

## Files

| Component               | Description                                                                                                                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lambda Function         | Main Lambda Function served on AWS Lambda. Grabs new annotations on AirTable, and makes file moves based on each table's annotations.                                                                         |
| AirTable S3 Integration | Generic Class that integrates with AirTable tables, with support to pull new annotations, record update, finalization, and patching through HTTP.                                                             |
| Audio Dashboard Table   | Takes annotated label (adult/child) and moves unlabeled files to respective folders. Also exports fixed transcripts, if any.                                                                                  |
| Disfluency Table        | Takes annotated label (addition/substitution/both/none) and moves unlabeled files to respective folders. Also exports fixed transcripts, if any.                                                              |
| Mispronunciations       | Additional utility to detect the type of mispronunciation contained within the audio. This takes the ground truth and the transcript of the audio. Returns either: addition, substitution, both, or none.     |
| Homophones              | During alignment comparison, homophones (same sounding words) are taken into account. This is to avoid any false negatives that might have just been homophones and thus obtain as many overlaps as possible. |
| S3 Utils                | Utility library to pull and push files from AWS S3.                                                                                                                                                           |

## Usage

Since this library is not meant to be used as an API endpoint, it requires a trigger. The trigger we used is a CRON job. Every 24 hours, the Lambda Function is invoked and annotations in AirTable are applied.

## API Reference

Please visit our [documentation](https://bookbot-kids.github.io/label-pipeline/reference/airtable_apply_annotations/lambda_function/) page for more details.