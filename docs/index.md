# Home

## Label Pipeline

<p align="center">
    <a href="https://github.com/bookbot-kids/label-pipeline/blob/main/LICENSE.md">
        <img alt="GitHub" src="https://img.shields.io/github/license/bookbot-kids/label-pipeline.svg?color=blue">
    </a>
    <a href="https://bookbot-kids.github.io/label-pipeline/">
        <img alt="Documentation" src="https://img.shields.io/website/http/bookbot-kids.github.io/label-pipeline.svg?down_color=red&down_message=offline&up_message=online">
    </a>
    <a href="https://github.com/bookbot-kids/label-pipeline/actions/workflows/tests.yml">
        <img alt="Tests" src="https://github.com/bookbot-kids/label-pipeline/actions/workflows/tests.yml/badge.svg">
    </a>
    <a href="https://codecov.io/gh/bookbot-kids/label-pipeline">
        <img alt="Code Coverage" src="https://img.shields.io/codecov/c/github/bookbot-kids/label-pipeline">
    </a>
    <a href="https://github.com/bookbot-kids/label-pipeline/blob/main/CODE_OF_CONDUCT.md">
        <img alt="Contributor Covenant" src="https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg">
    </a>
</p>


This repository hosts the necessary AWS Lambda scripts to facilitate an automated audio labeling pipeline. The main components of the pipeline includes:

| Component                                                                                                                       | Description                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Audio Transcription using AWS Transcribe](https://github.com/bookbot-kids/label-pipeline/tree/main/src/transcribe)             | Transcribe incoming audios stored in S3 using AWS Transcribe. After transcribing, align audios based on ground truth values and save annotations. |
| [Audio Splitting](https://github.com/bookbot-kids/label-pipeline/tree/main/src/audio_splitter)                                  | Based on audio alignment transcriptions, segment audios and split into different files before saving back to S3.                                  |
| [Audio Adult/Child Classifier](https://github.com/bookbot-kids/label-pipeline/tree/main/src/audio_classifier)                   | Classify incoming audios stored in S3 as either adult, or child audios.                                                                           |
| [Integration with AirTable Dashboards](https://github.com/bookbot-kids/label-pipeline/tree/main/src/airtable_apply_annotations) | Export AirTable audio annotations (transcript and labels) to S3 by moving files according to their labels.                                        |

For more details of each component, please check each subdirectory's README file.

## Pipeline Overview

The high-level overview of this pipeline is shown below.

![](images/audio-labeling-pipeline.png)

## Installation

```bash
git clone https://github.com/bookbot-kids/label-pipeline.git
cd label-pipeline
pip install -r requirements.txt
```

## References

```bib
@misc{label-studio-no-date,
	author = {{Label Studio}},
	title = {{Improve Audio Transcriptions with Label Studio}},
	url = {https://labelstud.io/blog/Improve-Audio-Transcriptions-with-Label-Studio.html},
}
```

## Contributors

<a href="https://github.com/bookbot-kids/label-pipeline/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=bookbot-kids/label-pipeline" />
</a>