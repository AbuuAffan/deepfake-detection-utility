from transformers import ViTForImageClassification, ViTImageProcessor, AutoImageProcessor, AutoModelForImageClassification
import os

# Hugging Face model repository to download
model_id = "dima806/deepfake_detector"
# Save next to this script in the directory expected by HFDetector
save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deepfake-vit-v2")

print(f"--- Starting download for {model_id} ---")

try:
    # 1. Download the 'Processor' (the part that prepares the image)
    processor = AutoImageProcessor.from_pretrained(model_id)
    processor.save_pretrained(save_path)

    # 2. Download the 'Model' (the brain itself)
    model = AutoModelForImageClassification.from_pretrained(model_id)
    model.save_pretrained(save_path)

    print(f"--- Success! Model saved to {os.path.abspath(save_path)} ---")
except Exception as e:
    print(f"Error downloading model: {e}")
    print("Please ensure you have internet connection and sufficient disk space")