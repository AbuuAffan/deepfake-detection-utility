"""Hugging Face Vision Transformer detector for deepfake detection"""

import os
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
from .base import BaseDetector


class HFDetector(BaseDetector):
    """Deepfake detector using Hugging Face advanced deepfake detection model"""
    
    # Class labels for the model
    CLASS_LABELS = {
        0: "Real",
        1: "Deepfake"
    }
    
    def __init__(self, model_path="./detector/models/deepfake-vit-v2"):
        """
        Initialize the HFDetector with a local advanced deepfake detection model.
        
        This model provides:
        - Higher accuracy for deepfake detection
        - More reliable confidence scores
        - Better generalization across different deepfake types
        
        Args:
            model_path: Path to the local model directory containing config.json,
                       model.safetensors/pytorch_model.bin, and preprocessor_config.json
        
        Raises:
            FileNotFoundError: If the model path does not exist
            OSError: If model loading fails
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path not found: {model_path}")
        
        self.model_path = model_path
        self.model_name = "Advanced Deepfake Detector (dima806)"
        self.version = "3.0.0"
        
        # Load processor and model from local path
        self.processor = AutoImageProcessor.from_pretrained(model_path)
        self.model = AutoModelForImageClassification.from_pretrained(model_path)
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        
        print(f"✓ Loaded {self.model_name} on device: {self.device}")
    
    def detect(self, file_path):
        """
        Detect if an image contains deepfake content with high confidence.
        
        Args:
            file_path: Path to the image file to analyze
        
        Returns:
            dict: Detection result with keys:
                - is_fake (bool): True if deepfake detected, False otherwise
                - confidence (float): Confidence score between 0.0 and 1.0
                - model (str): Name of the model used
                - predicted_class (str): "Deepfake" or "Real"
                - file_path (str): The analyzed file path
        
        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If the image format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        try:
            # Open and convert image to RGB
            image = Image.open(file_path).convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
        
        # Preprocess the image using the processor
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Run inference with no_grad for performance
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Get probabilities and predicted class
        probabilities = torch.softmax(logits, dim=-1)
        predicted_class_idx = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0, predicted_class_idx].item()
        
        # Determine if deepfake (index 1) or real (index 0)
        is_fake = predicted_class_idx == 1
        predicted_class_label = self.CLASS_LABELS.get(predicted_class_idx, "Unknown")
        
        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "model": self.model_name,
            "predicted_class": predicted_class_label,
            "file_path": file_path
        }
    
    def get_model_info(self):
        """
        Get information about the detection model.
        
        Returns:
            dict: Model information including name, version, and capabilities
        """
        return {
            "name": self.model_name,
            "version": self.version,
            "model_type": "Vision Transformer (ViT)",
            "model_path": self.model_path,
            "device": str(self.device),
            "classes": self.CLASS_LABELS,
            "capabilities": [
                "Image deepfake detection",
                "Binary classification (Deepfake/Realism)"
            ]
        }
