import torch
import numpy as np
import os
import gc
import time
import onnxruntime
from transformers import AutoModelForCausalLM, AutoTokenizer

# Set paths
pretrained_model_path = r"./model/AgentCPM-GUI"
onnx_visual_file_path = r'./model/AgentCPM_visual.onnx'
device = "cpu"

print(f"Starting ONNX conversion for AgentCPM-GUI visual processor...")
print(f"Model path: {pretrained_model_path}")
print(f"Output Visual ONNX path: {onnx_visual_file_path}")

try:
    # Load model
    print("Loading model (this may take a while)...")
    model = AutoModelForCausalLM.from_pretrained(
        pretrained_model_path,
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    
    # Export visual processor module to ONNX
    print("Extracting visual processor module...")
    model_visual = model.vpm.eval()
    model_visual = model_visual.to(device)
    
    # Sample input for the visual processor
    print("Creating dummy input...")
    dummy_input = torch.randn([1, 3, 364, 546]).to(device).half()
    
    # Export visual processor to ONNX
    print("Exporting visual processor to ONNX...")
    torch.onnx.export(
        model_visual,
        dummy_input,
        onnx_visual_file_path,
        opset_version=18,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {
                2: "height",
                3: "width",
            },
            "output": {1: "output_dim"},
        },
        do_constant_folding=True,
    )
    print(f"Visual processor exported to {onnx_visual_file_path}")
    
    # Verify the visual model
    print("Verifying visual ONNX model...")
    ort_session = onnxruntime.InferenceSession(onnx_visual_file_path)
    ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.cpu().numpy()}
    ort_outputs = ort_session.run(None, ort_inputs)
    print(f"Visual ONNX model verification successful. Output shape: {ort_outputs[0].shape}")
    
    print("\nONNX conversion completed successfully!")
    
except Exception as e:
    print(f"Error during conversion: {str(e)}")
    
finally:
    # Clean up
    print("Cleaning up resources...")
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
