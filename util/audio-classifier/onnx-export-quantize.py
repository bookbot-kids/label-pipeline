import onnxruntime
from onnxruntime.quantization import quantize_dynamic, QuantType
from transformers import AutoModelForAudioClassification
import torch
import numpy as np


def convert_to_onnx(
    model: torch.nn.Module, dummy_input: torch.Tensor, onnx_model_name: str
):
    """Converts PyTorch model to ONNX.

    Parameters
    ----------
    model : torch.nn.Module
        PyTorch model to be converted.
    dummy_input : torch.Tensor
        Dummy input of correct shape for model.
    onnx_model_name : str
        Save name of ONNX model.
    """
    print(f"Converting model to onnx")

    torch.onnx.export(
        model,  # model being run
        dummy_input,  # model input (or a tuple for multiple inputs)
        onnx_model_name,  # where to save the model (can be a file or file-like object)
        export_params=True,  # store the trained parameter weights inside the model file
        opset_version=11,  # the ONNX version to export the model to
        do_constant_folding=True,  # whether to execute constant folding for optimization
        input_names=["input"],  # the model's input names
        output_names=["output"],  # the model's output names
        dynamic_axes={
            "input": {1: "audio_len"},  # variable length axes
            "output": {1: "audio_len"},
        },
    )

    print(f"Converted model saved to {onnx_model_name}")


def quantize_onnx_model(onnx_model_path: str, quantized_model_path: str):
    """Quantizes ONNX model.

    Parameters
    ----------
    onnx_model_path : str
        Path to ONNX model.
    quantized_model_path : str
       Quantized ONNX model save name.
    """
    print("Starting quantization...")

    quantize_dynamic(
        onnx_model_path, quantized_model_path, weight_type=QuantType.QUInt8
    )

    print(f"Quantized model saved to {quantized_model_path}")


def test_onnx_model(
    onnx_model_path: str,
    dummy_input: torch.Tensor,
    dummy_output: torch.Tensor,
    quantized: bool = False,
):
    """Tests ONNX-converted model and the expected output.

    Parameters
    ----------
    onnx_model_path : str
        Path to ONNX model
    dummy_input : torch.Tensor
        Dummy Tensor input to the model.
    dummy_output : torch.Tensor
       Dummy desired output of the model, given input.
    quantized : bool, optional
        Is the model quantized? By default False
    """
    to_numpy = (
        lambda tensor: tensor.detach().cpu().numpy()
        if tensor.requires_grad
        else tensor.cpu().numpy()
    )

    ort_session = onnxruntime.InferenceSession(onnx_model_path)
    ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(dummy_input)}
    ort_outs = ort_session.run(None, ort_inputs)

    rtol = 1e-01 if quantized else 1e-03

    np.testing.assert_allclose(
        to_numpy(dummy_output), ort_outs[0], rtol=rtol, atol=1e-05
    )


def main():
    model_checkpoint = "bookbot/distil-wav2vec2-adult-child-cls-52m"
    onnx_model_name = model_checkpoint.split("/")[-1] + ".onnx"
    quantized_model_name = model_checkpoint.split("/")[-1] + ".quant.onnx"

    model = AutoModelForAudioClassification.from_pretrained(model_checkpoint)
    model.eval()

    # expected Tensor length
    audio_len = 48_000
    dummy_input = torch.randn(1, audio_len)

    # index to logit tensor
    output_tensor = model(dummy_input)[0]

    # convert to ONNX
    convert_to_onnx(model, dummy_input, onnx_model_name)
    test_onnx_model(onnx_model_name, dummy_input, output_tensor)

    # quantize model
    quantize_onnx_model(onnx_model_name, quantized_model_name)
    test_onnx_model(quantized_model_name, dummy_input, output_tensor, quantized=True)


if __name__ == "__main__":
    main()
