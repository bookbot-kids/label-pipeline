# Bookbot Audio Recording

## Background

Speech recognition is at the heart of the Bookbot app. This is how and where children’s speech is heard and compared with their intended text. Mispronunciations get detected, the app provides real-time reading feedback, and the child thus learns how to read. 

However, most readily available speech recognition services, such as those provided by Google, Amazon, or Azure, are only accessible online, hence requiring our users to have a stable internet connection. Moreover, though their accuracy in adult English speech is very high, we found that children’s speech and foreign languages like Indonesian tend to deteriorate in performance. 

Because speech recognition is the core of the Bookbot app and is critical to the performance of our learning system, we wanted to develop our own speech recognition model that does not only run offline but also one that accurately captures children’s speech which is a particularly niche domain.

In order to do so, it is crucial that we train our speech recognition model on a dataset that best reflects our intended user audience, namely children aged 4+. This brings about a new set of challenges -- that is, there are no publicly available, open-source children's speech data.

Therefore, this calls for our own audio recording project that aims to prepare an accurate dataset for speech recognition model training purposes.

## Methodology

### Speech Recording

The main source of our dataset comes from users that have been registered in our initial app testing sessions. Because we aim to gather as diverse of a dataset as possible, we have engaged with multiple schools across Indonesia. 

Students in Indonesia's public schools were introduced to the Bookbot app, onboarded, and are tasked to use the app as they learn to read. 160 students were tasked to read a minimum of 10 hours, within a 2-week time frame. All of these activities were done through the use of low-end mobile phones, which is the Bookbot app's main target platform.

In doing so, we attained a wide spectrum of variety within our data. For instance, different age groups, genders, dialects, reading capabilities, audio environments, etc. This would significantly increase the generalizability of our speech recognition model when deployed during production.

### Audio Grouping and Classification

The data which we have received after the recording session are still raw and uncleaned, calling for data cleaning and processing step. Firstly, data that comes in are grouped into their corresponding regions. We encode these regions based on (1) language and (2) region. For instance, children reading English texts in Australia are grouped into `en-AU`, and children reading Indonesian in Indonesia are grouped into `id-ID`. In doing so, we avoid confusion between the data files and train a speech recognition model on the intended language.

Afterward, we needed to filter the audio based on whether it is an adult's speech or children's speech. Ultimately, we only want children's speech as they are our intended target user. To do so, we deployed an open-source audio classifier model based on [Wav2Vec 2.0](https://arxiv.org/abs/2006.11477). This audio classifier was trained in-house and is able to distinguish between adult and children speech, with a reasonable accuracy after multiple tweaks in hyperparameters and architecture.

| Model                   | Accuracy | F1-Score |
| ----------------------- | :------: | :------: |
| Wav2Vec2 (Baseline)     |  95.80%  |  0.9618  |
| Wav2Vec2 XLS-R          |  94.69%  |  0.9508  |
| Distil Wav2Vec2 (Final) |  96.03%  |  0.9639  |

We served this model as an internal cloud service and is used to filter against incoming adult data.

During the training of the audio classifier, we also found the following distribution within the raw incoming data:

| Category            | Percentage |
| ------------------- | :--------: |
| Adult               |   42.8%    |
| Child               |   43.7%    |
| Delete (noise only) |   11.9%    |
| Mixed (>1 speaker)  |    1.6%    |

Notice that there are over 80% usable data (adult/child) from raw data.

### Transcribing and Alignment

A key challenge we needed to solve is ensuring that our data's labels are accurate. In theory, we could simply take the book's text (ground truth) that the children are reading and use that as the corresponding labels of our audio data. However, in practice, children often make reading disfluencies and this would lead to inaccurate labeling. While human-assisted labeling would do the job, it is impractical and potentially unsafe to employ tens of human annotators in the long term.

The alternative would be to use a more accurate speech recognizer/transcriber, for instance Amazon's AWS Transcribe service. But this too had its own set of limitations. As previously mentioned their accuracy on Indonesian children's speech is inadequate and would likely cause the same issues as the first option.

Therefore, we opted to develop our own algorithm that incorporates both AWS Transcribe and the book texts. After being transcribed, we compared the transcript with the ground truth and looked for overlaps. Those overlaps' timestamps were extracted and used to segment relevant audios, which are finally exported. This way, the automated algorithm is ensured to be as accurate as possible as it consults both a 100% accurate ground truth text (from books) and gets confirmed by a less accurate transcript with timestamps.

Finally, the segmented audios were exported as mono, 16-bit WAV files, with a sampling rate of 24 kHz. As a result, they are now usable for speech recognition training purposes.

### Improving Overlapping Audio Coverage

We implemented a few ways to improve the coverage of audio overlaps. Firstly, we considered the presence of homophones which may be inaccurately transcribed by AWS. By considering homophones as equal speeches, we managed to slightly increase the usable audio coverage, particularly for Indonesian recordings as homophones are common in the language.

Secondly, to improve the audio quality and avoid transcribing irrelevant parts of speech, we use the OS audio processing to remove speaker audio (Bookbot's bot) from the microphone channel. This way, we are only transcribing the necessary audios and ignore additional noise.

## Result

The following table summarizes the amount of clean data we have collected from this activity.

| Region  | No. of Audios | Total Raw Duration | Total Usable Duration | Size (GB) |
| ------- | ------------- | ------------------ | --------------------- | --------- |
| `id-ID` | 488,554       | 1145 h 50 min 0 s  | 219 h 19 min 43 s     | 49.5      |

With this data, we were able to significantly improve our speech recognition model's performance. Initially, the model's word-error rate (WER) is around 20-25% on synthetic (adult) test sets, and it is currently 15% on real-world children's speech test set -- which is an even harder task to solve. 

## Conclusion

The activity that we conducted with the help of Indonesian schools and their students have allowed us to create a speech recognition dataset that effectively models our intended user audience. Achieving a reasonably low WER, our open-source speech recognition model for children's speech could arguably outperform those provided by larger tech companies.

Likewise, this method could similarly be repeated for other specific low-resource target domains of speakers if needed, e.g. children's speech in Mandarin Chinese, Javanese, etc.