# Transcribe

This library is the core and unifier of the other libraries in this repository. It runs and end-to-end audio transcription using AWS Transcribe, audio classification, detects mispronunciations, and accounts for homophones. This library mostly delegates each task to their respective libraries, but it contains our main audio alignment algorithm. 

Particularly, it takes audio ground truths (e.g. from books) and transcriptions (e.g. what readers read), compares them, and tries to align as many audio chunks as possible. When those do meet, audios are subsequently chunked, classified into different speeches (adult/child), and mispronunciations are detected (addition/substitution/both/none).

**Note:** Like other components of this repository, this component is meant to be served as an AWS Lambda Function. However, it can still work if served on any other serverless cloud services. 

## Files

| Component         | Description                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lambda Function   | Main Lambda Function served on AWS Lambda. Pulls audio from S3, classifies it between adult/child. If child, the process stops and audio is archived. Otherwise, audios are transcribed, aligned with their ground truths, and then passed to audio splitter. If the audio also contains mispronunciations, an additional copy is also kept for further annotation purposes. |
| Transcribe        | Invokes an AWS Transcribe task, passing the newly arrived audio. Transcriptions are saved in AWS S3 and is used during alignment.                                                                                                                                                                                                                                            |
| Aligner           | Looks for overlaps between audio ground truth and transcription, greedily. This way, we find as many matching chunks as possible. A simple diff comparator was used.                                                                                                                                                                                                         |
| Homophones        | During alignment comparison, homophones (same sounding words) are taken into account. This is to avoid any false negatives that might have just been homophones and thus obtain as many overlaps as possible.                                                                                                                                                                |
| Classifier        | Invokes the audio classifier API and retrieves the adult/child classification result.                                                                                                                                                                                                                                                                                        |
| Mispronunciations | Additional utility to detect the type of mispronunciation contained within the audio. This takes the ground truth and the transcript of the audio. Returns either: addition, substitution, both, or none.                                                                                                                                                                    |
| S3 Utils          | Utility library to pull and push files from AWS S3.                                                                                                                                                                                                                                                                                                                          |
| SRT2TXT           | Utility library to convert `.srt` files to `.txt` if ever the transcriptions are of the former format (e.g. YouTube).                                                                                                                                                                                                                                                        |

## Usage

Since this library is not meant to be used as an API endpoint, it requires a trigger. The trigger we used is whenever a new audio file arrives at S3, and it runs the main Lambda Function.

## API Reference

Please visit our [documentation](https://bookbot-kids.github.io/label-pipeline/reference/transcribe/lambda_function/) page for more details.