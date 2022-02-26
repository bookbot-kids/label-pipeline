import json
import onnxruntime
from s3_utils import get_audio_file
import ffmpeg
import numpy as np


def read_audio_as_array(audio: str) -> np.ndarray:
    """Read audio from S3 url `audio`, resample to 16KHz, and return as Numpy array.

    Parameters
    ----------
    audio : str
        S3 audio URL.

    Returns
    -------
    np.ndarray
        Array of audio retrieved from S3.
    """
    # stream audio into ffmpeg
    stream = ffmpeg.input(audio)
    output = ffmpeg.output(
        stream, "pipe:", acodec="pcm_s16le", format="wav", ac=1, ar=16_000,
    )
    stdout, _ = output.run_async(pipe_stdout=True, pipe_stderr=True).communicate()

    # skip header bytes
    stdout = stdout[stdout.find(str.encode("data")) + 8 :]
    # convert bytes to numpy array
    # note: int16 because of s16le encoding used
    audio_array = np.frombuffer(stdout, np.int16).astype(np.float32)
    # normalize
    audio_array /= np.iinfo(np.int16).max

    return audio_array


def preprocess(audio_array: np.ndarray) -> np.ndarray:
    """Truncates/pads and normalizes audio array for classification using Wav2Vec2 model.

    Parameters
    ----------
    audio_array : np.ndarray
       Array of input audio.

    Returns
    -------
    np.ndarray
        Pre-processed audio array ready for classifier.
    """
    if len(audio_array) > 48_000:  # truncate
        audio_array = audio_array[:48_000]
    else:  # pad
        pad_length = 48_000 - len(audio_array)
        audio_array = np.pad(audio_array, (0, pad_length))

    normalized_audio = np.expand_dims(
        (audio_array - audio_array.mean(axis=0) / audio_array.std(axis=0)), axis=0
    )
    assert normalized_audio.shape == (1, 48_000)
    return normalized_audio


def predict(audio_array: np.ndarray, onnx_model_path: str) -> str:
    """Makes a prediction with ONNX model given audio array.

    Parameters
    ----------
    audio_array : np.ndarray
        Array of audio to be predicted.
    onnx_model_path : str
        Path to ONNX model predictor.

    Returns
    -------
    str
       Prediction, either "ADULT or "CHILD".
    """
    ort_session = onnxruntime.InferenceSession(onnx_model_path)
    ort_inputs = {ort_session.get_inputs()[0].name: audio_array}
    ort_outs = ort_session.run(None, ort_inputs)
    logits = ort_outs[0]
    predicted_idx = np.argmax(logits)

    id2label = {
        0: "ADULT",
        1: "CHILD",
    }

    prediction = id2label[predicted_idx]

    return {"prediction": prediction, "logits": logits.tolist()[0]}


def lambda_handler(event, context) -> str:
    """Event listener for S3 event and calls the daily logger function.

    Parameters
    ----------
    event : AWS Event
        A JSON-formatted document that contains data for a Lambda function to process.
    context : AWS Context
        An object that provides methods and properties that provide information about the invocation, function, and runtime environment.

    Returns
    -------
    str
       String-formatted JSON object containing statusCode and prediction.
    """
    try:
        audio_url = json.loads(event["body"])["audio_url"]
        audio = get_audio_file(audio_url)
        audio_array = read_audio_as_array(audio)
        if audio_array.size == 0:
            print(f"Audio {audio_url} is empty.")
            raise Exception
    except Exception as exc:
        response = {
            "statusCode": 400,
            "body": {"prediction": None, "error": "Failed to retrieve audio."},
        }
        return json.dumps(response)
    else:
        processed_audio = preprocess(audio_array)

        # onnx_model_path = "/opt/distil-wav2vec2-adult-child-cls-52m.quant.onnx"
        onnx_model_path = "../../models/distil-wav2vec2-adult-child-cls-52m.quant.onnx"
        results = predict(processed_audio, onnx_model_path)

        response = {"statusCode": 200, "body": results}
        return json.dumps(response)


if __name__ == "__main__":
    payload = {
        "audio_url": "s3://bookbot-speech/archive/en-au/381ed48d-0d1f-4f73-91d4-38c960d162fa_1645734280599.aac"
    }
    event = {"body": json.dumps(payload)}
    response = lambda_handler(event, None)
    print(response)
