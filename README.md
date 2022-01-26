# Label Pipeline

This repository hosts the necessary AWS Lambda scripts to facilitate an automated audio labeling pipeline. The main components of the pipeline includes:

- [Audio Transcription using AWS Transcribe](https://github.com/bookbot-kids/label-pipeline/tree/main/src/transcribe)

- [Label Studio Webhook Integration](https://github.com/bookbot-kids/label-pipeline/tree/main/src/webhook_listener)

- [Audio Splitting](https://github.com/bookbot-kids/label-pipeline/tree/main/src/audio_splitter)

# Overview

The high-level overview of this pipeline is shown below.

![](./images/audio-labeling-pipeline.png)

# Structure

```bash
.
├── README.md
├── images
│   └── audio-labeling-pipeline.png
├── requirements.txt
├── src
│   ├── audio_splitter
│   │   └── lambda_function.py
│   ├── config.py
│   ├── step_function_invoker
│   │   └── lambda_function.py
│   ├── transcribe
│   │   ├── homophones.py
│   │   ├── lambda_function.py
│   │   ├── mispronunciation.py
│   │   └── srt2txt.py
│   └── webhook_listener
│       └── lambda_function.py
├── tests
│   ├── audio_splitter
│   │   ├── test-event-1.json
│   │   └── test-event-2.json
│   ├── step_function_invoker
│   │   └── test-event-1.json
│   └── transcribe
│       ├── mispronunciation_test.py
│       ├── test-event-1.json
│       ├── test-event-2.json
│       ├── test-event-3.json
│       └── test-event-4.json
└── util
    ├── label-studio
    │   └── audio-transcription-segment-interface.js
    ├── s3
    │   └── CORS.json
    ├── stepfunctions
    │   └── transcribe.asl
    └── transcribe
        └── special_words.txt
```
