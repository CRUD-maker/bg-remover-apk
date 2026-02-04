import onnxruntime as ort
import numpy as np
from PIL import Image
import os
import requests

# URL for the U2Net ONNX model (Standard)
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
MODEL_NAME = "u2net.onnx"

class MobileRemover:
    def __init__(self):
        self.session = None
        self._ensure_model()

    def _ensure_model(self):
        """Check if model exists, else download it."""
        if not os.path.exists(MODEL_NAME):
            print("Downloading model...")
            response = requests.get(MODEL_URL)
            with open(MODEL_NAME, "wb") as f:
                f.write(response.content)
            print("Model downloaded.")
        
        # Initialize session
        # On Android, we might need to restrict threads
        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = 2
        self.session = ort.InferenceSession(MODEL_NAME, sess_options, providers=['CPUExecutionProvider'])

    def process_image(self, img_path):
        """
        Run inference directly using ONNX Runtime.
        This bypasses 'rembg' library to avoid Scipy/NDK issues.
        """
        # 1. Preprocess
        img = Image.open(img_path).convert("RGB")
        original_size = img.size
        
        # Resize to 320x320 (U2Net standard input)
        img_resized = img.resize((320, 320), Image.Resampling.BILINEAR)
        
        # Normalize
        img_np = np.array(img_resized).astype(np.float32)
        img_np /= 255.0
        
        # Mean subtraction (standard ImageNet means) - actually U2Net uses specific mean?
        # rembg implementation uses: (x - mean) / std
        # But simple normalization 0-1 works "okay" for u2net generally, 
        # let's try to match rembg preprocessing exactly if possible.
        # rembg: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        
        img_np -= np.array([0.485, 0.456, 0.406], dtype=np.float32)
        img_np /= np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
        # CHW format
        img_np = img_np.transpose((2, 0, 1))
        img_np = np.expand_dims(img_np, axis=0) # Batch dim
        
        # 2. Inference
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name
        
        masks = self.session.run([output_name], {input_name: img_np})
        mask = masks[0][0] # First batch, first channel
        
        # 3. Postprocess Mask
        # Sigmoid
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))
            
        mask = sigmoid(mask)
        
        # Squeeze
        mask = np.squeeze(mask)
        
        # Convert to PIL
        mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode='L')
        
        # Resize mask back to original size
        mask_img = mask_img.resize(original_size, Image.Resampling.LANCZOS)
        
        # 4. Composite
        final_img = Image.open(img_path).convert("RGBA")
        final_img.putalpha(mask_img)
        
        return final_img
