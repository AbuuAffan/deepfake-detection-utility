"""Main entry point for Deepfake Detection Utility"""

import customtkinter as ctk
from gui.app import DeepfakeDetectorApp
from detector import HFDetector

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def main():
    """Main entry point"""
    # Initialize detector with local Vision Transformer model
    detector = HFDetector()
    
    # Create and run the application
    app = DeepfakeDetectorApp(detector=detector)
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()


if __name__ == "__main__":
    main()

