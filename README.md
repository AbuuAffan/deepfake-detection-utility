# Deepfake Detection Utility

A professional, scalable Python application for deepfake detection with a draggable floating action button (FAB) overlay and multi-monitor screen capture support.

## Architecture

The application follows a modular, scalable architecture:

```
Deepfake/
├── main.py                 # Entry point
├── gui/                    # UI Components
│   ├── __init__.py
│   ├── app.py             # Main application window
│   ├── ask_button.py      # Draggable FAB component
│   └── capture_overlay.py # Screen capture overlay
├── capture/                # Capture Engine
│   ├── __init__.py
│   └── engine.py          # Screen/media capture logic
├── detector/               # Detection Models
│   ├── __init__.py
│   ├── base.py            # Base detector interface
│   ├── hf_detector.py     # Vision Transformer detector (active)
│   └── models/
│       ├── download_model.py
│       └── deepfake-vit-v2/  # Local ViT model (config + weights)
└── captures/              # Output directory (auto-created)
```

## Features

- **Local Vision Transformer**: Uses a locally-hosted ViT model for deepfake detection
- **GPU Acceleration**: Automatically uses CUDA when available, falls back to CPU
- **Modular Architecture**: Clean separation of UI, capture, and detection logic
- **Swappable Detectors**: Easy to swap detection models (API vs Local) without touching GUI code
- **Multi-Monitor Support**: Full-screen overlay works across all connected monitors
- **Draggable FAB**: Floating action button that stays on top of all windows
- **Native UX**: Dimmed screen with clear selection box (Windows/macOS style)
- **Professional Structure**: Startup-ready codebase with clear interfaces

## Requirements

- Python 3 (use a version supported by the installed PyTorch and Transformers releases)
- CustomTkinter
- MSS (for screen capture)
- Pillow (for image processing)
- PyTorch
- Transformers (Hugging Face)
- Safetensors (for model loading)

## Installation

Run these commands from the project root. Create and activate a virtual environment, then install the packages listed in `requirements.txt`:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The requirements include CustomTkinter, MSS, Pillow, PyTorch, Transformers, and Safetensors. PyTorch uses CUDA when available and otherwise runs on CPU.

## Downloading the Model

The application expects the model and processor files under `detector/models/deepfake-vit-v2/`. After installing dependencies, run the downloader from the project root:

```bash
python detector/models/download_model.py
```

The script downloads the processor and model from `dima806/deepfake_detector` on Hugging Face and saves them in the expected model directory. This step requires internet access and enough disk space. Confirm that the directory contains `config.json`, `preprocessor_config.json`, and the model weights (normally `model.safetensors`) before starting the application.

### Model Attribution and License

The configured upstream model is [`dima806/deepfake_detector`](https://huggingface.co/dima806/deepfake_detector) on Hugging Face (repository namespace: `dima806`). The checked-in model configuration and processor files do not state a license, and no license is asserted here. Check the upstream model page and its current license/terms before using or redistributing the downloaded weights. The project code's license, if any, does not by itself establish the model weights' license.

## Usage

### Running the Application

With the virtual environment activated and model downloaded, run from the project root:

```bash
python main.py
```

The detector loads the local model during startup. The first launch will fail if the model directory or required files are missing.

### Using a Custom Detector

To use your own detection model, simply implement the `BaseDetector` interface:

```python
from detector.base import BaseDetector

class MyDetector(BaseDetector):
    def detect(self, file_path):
        # Your detection logic here
        return {
            "is_fake": True,
            "confidence": 0.98,
            "model": "MyModel"
        }

    def get_model_info(self):
        return {"name": "MyModel", "version": "1.0"}
```

Then in `main.py`:

```python
from detector.my_detector import MyDetector

detector = MyDetector()
app = DeepfakeDetectorApp(detector=detector)
app.run()
```

## How It Works

1. **Toggle ON** to show the draggable Ask button overlay
2. **Drag** the Ask button to position it anywhere on your screen
3. **Click ASK** to capture a screen area
4. **Select area** by dragging on the dimmed overlay
5. **Vision Transformer Analysis**: The local ViT model analyzes the image
   - Image is preprocessed and resized
   - Model runs inference in `torch.no_grad()` mode for performance
   - Model configuration maps index 0 to Realism and index 1 to Deepfake
6. **Results** are displayed with confidence score
   - ⚠️ Deepfake detected (with confidence %)
   - ✓ Authentic (with confidence %)

### Privacy

Selected screen areas are saved as timestamped PNG files in the local `captures/` directory. They are not automatically deleted when the application closes. Detection uses the downloaded local model and does not send captures to a remote inference API. The downloader does contact Hugging Face to retrieve the model files.

## Project Structure

### GUI Package (`gui/`)

- **`app.py`**: Main application window that coordinates all components
- **`ask_button.py`**: Draggable floating action button
- **`capture_overlay.py`**: Multi-monitor screen capture overlay

### Capture Package (`capture/`)

- **`engine.py`**: Handles screen capture using MSS; video capture is not implemented

### Detector Package (`detector/`)

- **`base.py`**: Abstract base class defining the detector interface
- **`hf_detector.py`**: Vision Transformer detector using local model
  - Loads model from `detector/models/deepfake-vit-v2/`
  - Model config mapping: Realism (index 0) and Deepfake (index 1)
  - GPU/CPU adaptive with `torch.no_grad()` optimization
  - Note: the detector's result label for index 0 is currently `"Real"`; this is the same non-deepfake class named `"Realism"` in the model config.

## Extending the Application

### Current Detector: HFDetector

The application currently uses the **HFDetector** (Hugging Face Vision Transformer):

```python
from detector import HFDetector

detector = HFDetector()  # Loads from ./detector/models/deepfake-vit-v2
result = detector.detect("image.jpg")

# Returns:
# {
#     "is_fake": True/False,
#     "confidence": 0.95,
#     "model": "Vision Transformer Deepfake Detector",
#     "predicted_class": "Deepfake" or "Real",
#     "file_path": "image.jpg"
# }
```

### Switching to a Different Detector

1. Create a new detector file in `detector/` (e.g., `api_detector.py`)
2. Inherit from `BaseDetector`
3. Implement `detect()` and `get_model_info()` methods
4. Update `main.py` to import and use your detector instead of HFDetector

### Adding Video Support

Video support is not implemented. `CaptureEngine.capture_video()` currently raises `NotImplementedError`, and `HFDetector` processes images only.

## Notes

- The Ask button uses `overrideredirect(True)` to remove window decorations
- The button is set to always stay on top using `wm_attributes("-topmost", True)`
- Uses CustomTkinter only (no PyQt/Qt dependencies)
- Selected screen captures are saved locally with timestamps in the `captures/` folder and are not automatically removed

## Troubleshooting

- **Model path or files not found:** From the project root, run `python detector/models/download_model.py` and verify the files are in `detector/models/deepfake-vit-v2/`.
- **Missing Python package:** Activate the project's virtual environment and run `pip install -r requirements.txt`.
- **Download fails:** Check internet access to Hugging Face and available disk space, then retry the downloader.
- **CUDA/GPU errors or no compatible GPU:** The detector falls back to CPU when CUDA is unavailable. CPU inference may take longer.
- **Capture fails or is blank:** Ensure screen capture is permitted by the operating system and try selecting a non-empty screen area.

## Future Work

Make it for full screen image
increase the accuracy
implement for video part( record the screen stream frame by frame during recording analyse frame by frame then after sometime{need to think about how much time it should take to give analysis result} show the result in the screen )
