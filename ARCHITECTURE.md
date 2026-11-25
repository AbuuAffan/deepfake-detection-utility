# Architecture Guide

## Overview

The Deepfake Detection Utility follows a clean, modular architecture that separates concerns:

- **GUI Layer**: Handles all user interface components
- **Capture Layer**: Manages screen/media capture functionality
- **Detector Layer**: Abstract interface for detection models (swappable)

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│           main.py (Entry Point)         │
│  - Initializes detector                 │
│  - Creates and runs app                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         gui/app.py (Main App)           │
│  - Coordinates UI components            │
│  - Handles detection results            │
│  - Manages application state            │
│  - Threading for non-blocking detection │
└──────┬──────────────────┬───────────────┘
       │                  │
       ▼                  ▼
┌──────────────┐  ┌──────────────────────┐
│ ask_button   │  │  capture_overlay     │
│ (Draggable   │  │  (Screen Selection)  │
│  FAB)        │  │                      │
└──────────────┘  └──────────┬───────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │  capture/engine.py   │
                    │  (MSS Capture)       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  detector/           │
                    │  (BaseDetector)      │
                    │  - detect()          │
                    │  - get_model_info()  │
                    └──────────────────────┘
```

## Key Design Principles

### 1. Separation of Concerns

- **GUI** doesn't know about detection models
- **Capture** doesn't know about GUI
- **Detector** is completely independent

### 2. Interface-Based Design

- All detectors implement `BaseDetector`
- Easy to swap implementations
- No changes needed to GUI when switching models

### 3. Dependency Injection

- Detector is injected into the App
- Makes testing easier
- Allows runtime model selection

### 4. Asynchronous Detection

- Detection runs in background threads to prevent GUI freezing
- UI updates happen on main thread using `root.after()`
- Proper error handling between threads
- Visual feedback during processing

## Threading Implementation

### Background Detection Process

The application uses threading to ensure the GUI remains responsive during detection operations:

```python
# Main thread: on_capture_complete()
def on_capture_complete(self, capture_path):
    # Update UI immediately
    self.status_label.configure(text="Analyzing... Please wait.", text_color="orange")

    # Start background thread
    detection_thread = threading.Thread(
        target=self.run_detection_thread,
        args=(capture_path,),
        daemon=True
    )
    detection_thread.start()

# Background thread: run_detection_thread()
def run_detection_thread(self, capture_path):
    try:
        result = self.detector.detect(capture_path)
        result["filename"] = os.path.basename(capture_path)
        # Pass back to main thread
        self.root.after(0, self.update_results_ui, result)
    except Exception as e:
        error_result = {"error": str(e), "filename": os.path.basename(capture_path)}
        self.root.after(0, self.update_results_ui, error_result)

# Main thread: update_results_ui()
def update_results_ui(self, result):
    # Safe UI updates on main thread
    if "error" in result:
        self.status_label.configure(text=f"Detection error: {result['error']}", text_color="red")
    else:
        # Update with detection results
        confidence = result.get("confidence", 0.0)
        if result.get("is_fake", False):
            self.status_label.configure(text=f"⚠️ Deepfake detected! ({confidence:.1%} confidence)", text_color="red")
        else:
            self.status_label.configure(text=f"✓ Authentic ({confidence:.1%} confidence)", text_color="green")
```

### Thread Safety Considerations

- **UI Updates**: All UI modifications happen on the main thread using `root.after()`
- **Background Threads**: Detection runs in daemon threads that don't prevent app exit
- **Error Handling**: Exceptions are caught in background thread and passed to main thread
- **Visual Feedback**: Status indicator changes color during processing (orange → green/red)

### Benefits of Threading

1. **Responsive UI**: Application remains interactive during long-running detections
2. **API Compatibility**: Supports time-consuming API calls without freezing
3. **User Experience**: Clear visual feedback shows processing status
4. **Error Resilience**: Proper exception handling prevents crashes
5. **Scalability**: Can handle multiple detection requests without blocking

## Current Implementation: HFDetector

### Vision Transformer Deepfake Detector

The application currently uses **HFDetector** with a locally-hosted Vision Transformer model:

```python
# detector/hf_detector.py
from detector.base import BaseDetector
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image

class HFDetector(BaseDetector):
    def __init__(self, model_path="./detector/models/deepfake-vit-v2"):
        # Load processor and model from local path
        self.processor = AutoImageProcessor.from_pretrained(model_path)
        self.model = AutoModelForImageClassification.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        self.model.eval()

    def detect(self, file_path):
        # Convert to RGB
        image = Image.open(file_path).convert("RGB")

        # Preprocess
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Inference with no_grad for performance
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits

        # Model config: 0=Realism, 1=Deepfake
        probabilities = torch.softmax(logits, dim=-1)
        predicted_class_idx = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0, predicted_class_idx].item()
        is_fake = predicted_class_idx == 1

        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "model": "Vision Transformer Deepfake Detector",
            "predicted_class": "Deepfake" if is_fake else "Real",
            "file_path": file_path
        }
```

**Key Features:**

- GPU acceleration (CUDA when available, CPU fallback)
- `torch.no_grad()` for optimal inference performance
- Model config mapping: Realism (index 0) and Deepfake (index 1)
- The detector treats index 1 as fake; its current display-label table calls index 0 `"Real"` rather than the config's `"Realism"`
- Uses local model at `./detector/models/deepfake-vit-v2/`
- Inference uses the local model; downloading its weights requires internet access

The configured upstream model is `dima806/deepfake_detector` on Hugging Face. The checked-in model configuration and processor files do not declare a license; verify the upstream model page's current license and terms before use or redistribution. See the installation and model-download instructions in `README.md`.

## Switching to a Different Detector

To use a different detector, follow these steps:

### Step 1: Create Your Detector Class

```python
# detector/my_detector.py
from detector.base import BaseDetector

class MyAPIDetector(BaseDetector):
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_name = "MyAPIModel"

    def detect(self, file_path):
        # Your API call logic here
        response = call_api(file_path, self.api_key)

        return {
            "is_fake": response["is_fake"],
            "confidence": response["confidence"],
            "model": self.model_name,
            "api_response": response  # Additional metadata
        }

    def get_model_info(self):
        return {
            "name": self.model_name,
            "version": "1.0.0",
            "type": "api",
            "capabilities": ["image", "video"]
        }
```

### Step 2: Register in `detector/__init__.py`

```python
from .my_detector import MyAPIDetector

__all__ = ['BaseDetector', 'HFDetector', 'MyAPIDetector']
```

### Step 3: Update `main.py`

```python
from detector import MyAPIDetector

detector = MyAPIDetector(api_key="your-api-key")
app = DeepfakeDetectorApp(detector=detector)
app.run()
```

## Adding Video Support

### In CaptureEngine

The `CaptureEngine.capture_video()` method is a placeholder and raises `NotImplementedError`. The current `HFDetector` opens image files with Pillow, so video detection is not implemented.

```python
def capture_video(self, video_path):
    """Capture/process a video file"""
    # Implement video capture/processing here
    raise NotImplementedError("Video capture not yet implemented")
```

### In BaseDetector

The `detect()` method receives a file path, but the interface alone does not provide video support. Future video support would need a video decoder and a detector implementation that samples or processes frames:

```python
def detect(self, file_path):
    # file_path can be image or video
    # Your implementation should handle both
    pass
```

## Testing

Automated tests can provide a test double implementing `BaseDetector`; tests of `HFDetector` require a local model directory and image input.

## File Structure

```
Deepfake/
├── main.py                    # Entry point (uses HFDetector)
├── gui/                       # UI Components
│   ├── __init__.py
│   ├── app.py                # Main application
│   ├── ask_button.py         # Draggable FAB
│   └── capture_overlay.py    # Screen overlay
├── capture/                   # Capture Engine
│   ├── __init__.py
│   └── engine.py             # MSS capture logic
├── detector/                  # Detection Models
│   ├── __init__.py
│   ├── base.py               # Abstract interface
│   ├── hf_detector.py        # Vision Transformer detector (ACTIVE)
│   ├── models/
│   │   ├── download_model.py
│   │   └── deepfake-vit-v2/  # Local ViT model
│   │       ├── config.json
│   │       ├── model.safetensors
│   │       └── preprocessor_config.json
│   └── [other_detectors].py  # Future implementations
└── captures/                  # Output directory
```

## Benefits of This Architecture

1. **Scalability**: Easy to add new features without breaking existing code
2. **Testability**: Each component can be tested independently
3. **Maintainability**: Clear separation makes code easier to understand
4. **Flexibility**: Swap detectors, capture methods, or UI components easily
5. **Team Collaboration**: Different developers can work on different layers

## Migration from Old Code

The old `deepfake_detector.py` file is preserved for reference. All functionality has been moved to the new structure:

- `DraggableAskButton` → `gui/ask_button.py`
- `ScreenCaptureOverlay` → `gui/capture_overlay.py`
- `DeepfakeDetectorApp` → `gui/app.py`
- Capture logic → `capture/engine.py`
- Detection interface → `detector/base.py`

## Model Loading and Inference

### Local Model Path

The HFDetector automatically loads the Vision Transformer model from:

```
./detector/models/deepfake-vit-v2/
```

This directory contains:

- `config.json` - Model architecture configuration
- `model.safetensors` - Pre-trained model weights (secure format)
- `preprocessor_config.json` - Image processor configuration

### Inference Pipeline

1. **Image Loading**: Opens file and converts to RGB format
2. **Preprocessing**: AutoImageProcessor resizes and normalizes the image
3. **GPU Placement**: Moves tensors to GPU if available
4. **Inference**: Runs model in `torch.no_grad()` context (no gradient computation)
5. **Softmax**: Converts logits to probabilities
6. **Classification**: The model config maps index 0 to Realism and index 1 to Deepfake. `HFDetector` treats index 1 as fake; its current display label for index 0 is `"Real"`.
7. **Confidence**: Extracts probability score for the predicted class

### Performance Optimization

- `torch.no_grad()`: Disables gradient tracking for faster inference
- GPU acceleration: CUDA tensor operations when available
- Lazy model initialization: Loads on first use, not at startup
