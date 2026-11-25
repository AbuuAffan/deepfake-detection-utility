"""Main application window"""

import customtkinter as ctk
import os
import threading
from .ask_button import DraggableAskButton
from .capture_overlay import ScreenCaptureOverlay


class DeepfakeDetectorApp:
    """Main application window"""
    
    def __init__(self, detector=None):
        """
        Initialize the application.
        
        Args:
            detector: Detector instance (BaseDetector). If None, uses HFDetector.
        """
        from detector import HFDetector
        
        self.root = ctk.CTk()
        self.root.title("Deepfake Detection Utility")
        self.root.geometry("500x300")
        
        # Initialize detector (use provided or default to HFDetector)
        self.detector = detector if detector is not None else HFDetector()
        
        # Initialize components
        self.ask_button = None
        self.capture_overlay = None
        self.toggle_var = ctk.BooleanVar(value=False)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Deepfake Detection Utility",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Toggle the switch to show/hide the Ask button overlay",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc_label.pack(pady=10)
        
        # Toggle switch
        toggle_frame = ctk.CTkFrame(main_frame)
        toggle_frame.pack(pady=30)
        
        toggle_label = ctk.CTkLabel(
            toggle_frame,
            text="Show Ask Button:",
            font=ctk.CTkFont(size=16)
        )
        toggle_label.pack(side="left", padx=10)
        
        toggle_switch = ctk.CTkSwitch(
            toggle_frame,
            text="",
            variable=self.toggle_var,
            command=self.on_toggle_changed,
            width=60
        )
        toggle_switch.pack(side="left", padx=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Status: Ask button is hidden",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=20)
        
        # Instructions
        instructions = ctk.CTkTextbox(
            main_frame,
            height=80,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        instructions.pack(pady=10, padx=20, fill="both", expand=True)
        instructions.insert("1.0", "Instructions:\n• Toggle ON to show the draggable Ask button\n• Drag the Ask button to position it anywhere\n• Click ASK to capture a screen area\n• The Ask button stays on top of all windows")
        instructions.configure(state="disabled")
    
    def on_toggle_changed(self):
        """Handle toggle switch changes"""
        if self.toggle_var.get():
            # Show Ask button
            if self.ask_button is None:
                self.ask_button = DraggableAskButton(self.root, self.on_capture_requested)
            self.ask_button.show()
            self.status_label.configure(text="Status: Ask button is visible", text_color="green")
        else:
            # Hide Ask button
            if self.ask_button:
                self.ask_button.hide()
            self.status_label.configure(text="Status: Ask button is hidden", text_color="gray")
    
    def on_capture_requested(self):
        """Handle capture request from Ask button"""
        if self.capture_overlay is None:
            self.capture_overlay = ScreenCaptureOverlay(self.root, self.on_capture_complete)
        self.capture_overlay.show()
    
    def on_capture_complete(self, capture_path):
        """Handle capture completion and run detection"""
        if os.path.exists(capture_path):
            filename = os.path.basename(capture_path)
            self.status_label.configure(
                text="Analyzing... Please wait.",
                text_color="orange"
            )
            
            # Start detection in a background thread
            detection_thread = threading.Thread(
                target=self.run_detection_thread,
                args=(capture_path,),
                daemon=True
            )
            detection_thread.start()
        else:
            self.status_label.configure(
                text="Capture failed",
                text_color="red"
            )
    
    def run_detection_thread(self, capture_path):
        """Run detection in background thread"""
        try:
            # Run detection
            result = self.detector.detect(capture_path)
            
            # Add filename to result for UI update
            result["filename"] = os.path.basename(capture_path)
            
            # Pass result back to main thread for UI update
            self.root.after(0, self.update_results_ui, result)
            
        except Exception as e:
            # Pass error back to main thread
            error_result = {"error": str(e), "filename": os.path.basename(capture_path)}
            self.root.after(0, self.update_results_ui, error_result)
    
    def update_results_ui(self, result):
        """Update UI with detection results (runs on main thread)"""
        if "error" in result:
            self.status_label.configure(
                text=f"Detection error: {result['error']}",
                text_color="red"
            )
            print(f"Detection error: {result['error']}")
            return
        
        filename = os.path.basename(result.get("filename", "unknown"))
        
        # Update UI with results
        if result.get("is_fake", False):
            confidence = result.get("confidence", 0.0)
            self.status_label.configure(
                text=f"⚠️ Deepfake detected! ({confidence:.1%} confidence) - {filename}",
                text_color="red"
            )
        else:
            confidence = result.get("confidence", 0.0)
            self.status_label.configure(
                text=f"✓ Authentic ({confidence:.1%} confidence) - {filename}",
                text_color="green"
            )
        
        # Print detailed result to console
        print(f"\nDetection Result for {filename}:")
        print(f"  Is Fake: {result.get('is_fake', False)}")
        print(f"  Confidence: {result.get('confidence', 0.0):.2%}")
        print(f"  Model: {result.get('model', 'Unknown')}")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if self.ask_button:
            self.ask_button.destroy()
        self.root.destroy()

