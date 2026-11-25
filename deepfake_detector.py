import customtkinter as ctk
import tkinter as tk
import mss
from PIL import Image
import os
from datetime import datetime
import time

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DraggableAskButton:
    """Draggable floating action button that stays on top of all windows"""
    
    def __init__(self, parent, capture_callback):
        self.parent = parent
        self.capture_callback = capture_callback
        self.window = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.start_x = 0
        self.start_y = 0
        self.drag_threshold = 5  # pixels
        
    def create(self):
        """Create the draggable Ask button window - styled as a Floating Pill"""
        if self.window is None or not self.window.winfo_exists():
            self.window = ctk.CTkToplevel(self.parent)
            self.window.overrideredirect(True)  # Remove window decorations
            self.window.attributes("-topmost", True)  # Always on top
            self.window.attributes("-alpha", 0.8)  # Semi-transparent
            
            # Make window pill-shaped (wider than tall)
            self.window.geometry("100x50")
            
            # Configure window background - dark semi-transparent
            self.window.configure(bg="#2b2b2b")
            
            # Create a frame with rounded corners to act as the pill container
            self.pill_frame = ctk.CTkFrame(
                self.window,
                fg_color="#1a1a1a",  # Dark background
                corner_radius=25,  # Highly rounded for pill shape
                border_width=2,  # Subtle border
                border_color="#4a4a4a"  # Subtle border color
            )
            self.pill_frame.pack(fill="both", expand=True, padx=2, pady=2)
            
            # Create the Ask button/label (without command, we'll handle it manually)
            self.ask_button = ctk.CTkLabel(
                self.pill_frame,
                text="🔍 ASK",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                text_color="white",
                cursor="hand2"
            )
            self.ask_button.pack(expand=True, fill="both")
            
            # Bind mouse events for dragging on the window
            self.window.bind("<Button-1>", self.start_drag)
            self.window.bind("<B1-Motion>", self.on_drag)
            self.window.bind("<ButtonRelease-1>", self.on_release)
            
            # Bind dragging to pill frame and button as well
            self.pill_frame.bind("<Button-1>", self.start_drag)
            self.pill_frame.bind("<B1-Motion>", self.on_drag)
            self.pill_frame.bind("<ButtonRelease-1>", self.on_release)
            self.ask_button.bind("<Button-1>", self.start_drag)
            self.ask_button.bind("<B1-Motion>", self.on_drag)
            self.ask_button.bind("<ButtonRelease-1>", self.on_release)
            
            # Position at center of screen initially
            self.center_window()
            
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def start_drag(self, event):
        """Start dragging the window"""
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.drag_start_x = event.x_root - self.window.winfo_x()
        self.drag_start_y = event.y_root - self.window.winfo_y()
        return "break"  # Prevent event propagation
    
    def on_drag(self, event):
        """Handle window dragging - smooth dragging without flickering"""
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        # Update geometry without forcing redraw to reduce flickering
        self.window.geometry(f"+{x}+{y}")
        self.window.update_idletasks()
        return "break"  # Prevent event propagation
    
    def on_release(self, event):
        """Handle mouse release - check if it was a click or drag"""
        # Calculate movement distance
        dx = abs(event.x_root - self.start_x)
        dy = abs(event.y_root - self.start_y)
        
        # If movement is less than threshold, it's a click
        if dx < self.drag_threshold and dy < self.drag_threshold:
            self.on_ask_clicked()
        return "break"  # Prevent event propagation
    
    def on_ask_clicked(self):
        """Handle Ask button click - minimize and trigger capture"""
        if self.window:
            # Hide the Ask button temporarily
            self.window.withdraw()
            # Trigger capture callback
            self.capture_callback()
            # Re-show the button after a short delay
            self.parent.after(100, self.show_button)
    
    def show_button(self):
        """Re-show the Ask button after capture"""
        if self.window:
            self.window.deiconify()
    
    def show(self):
        """Show the Ask button window"""
        if self.window:
            self.window.deiconify()
        else:
            self.create()
    
    def hide(self):
        """Hide the Ask button window"""
        if self.window:
            self.window.withdraw()
    
    def destroy(self):
        """Destroy the Ask button window"""
        if self.window:
            self.window.destroy()
            self.window = None


class ScreenCaptureOverlay:
    """Multi-monitor aware transparent full-screen overlay for drag-and-select screen capture"""
    
    def __init__(self, parent, capture_callback):
        self.parent = parent
        self.capture_callback = capture_callback
        self.overlay = None
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.canvas = None
        self.monitors = []
        self.virtual_width = 0
        self.virtual_height = 0
        self.virtual_left = 0
        self.virtual_top = 0
        
    def get_multi_monitor_geometry(self):
        """Detect all monitors and calculate virtual desktop bounding box"""
        with mss.mss() as sct:
            # Get all monitors - monitor 0 is the combined virtual desktop
            all_monitors = sct.monitors
            
            if len(all_monitors) > 1:
                # Multiple monitors detected - use individual monitors
                self.monitors = all_monitors[1:]  # Skip monitor 0 (all monitors combined)
            else:
                # Single monitor - use monitor 0
                self.monitors = [all_monitors[0]]
            
            # Calculate virtual desktop bounding box
            lefts = [m['left'] for m in self.monitors]
            tops = [m['top'] for m in self.monitors]
            rights = [m['left'] + m['width'] for m in self.monitors]
            bottoms = [m['top'] + m['height'] for m in self.monitors]
            
            self.virtual_left = min(lefts)
            self.virtual_top = min(tops)
            self.virtual_width = max(rights) - self.virtual_left
            self.virtual_height = max(bottoms) - self.virtual_top
    
    def show(self):
        """Show the capture overlay - multi-monitor aware with native UX"""
        # Clean up any existing overlay first
        if self.overlay:
            self.hide()
        
        self.overlay = tk.Toplevel(self.parent)
        
        # Get multi-monitor geometry
        self.get_multi_monitor_geometry()
        
        # Set overlay to cover ENTIRE virtual desktop
        self.overlay.geometry(f"{self.virtual_width}x{self.virtual_height}+{self.virtual_left}+{self.virtual_top}")
        self.overlay.overrideredirect(True)  # Frameless
        self.overlay.attributes("-topmost", True)  # Stay on top
        self.overlay.attributes("-alpha", 0.3)  # Smooth dimming (native style)
        self.overlay.configure(bg="black")
        
        # Initialize canvas to None first, then create it
        self.canvas = None
        self.rect_id = None
        
        # Create canvas for drawing selection rectangle
        self.canvas = tk.Canvas(
            self.overlay,
            highlightthickness=0,
            bg="black",
            cursor="crosshair",  # Crosshair cursor for native UX
            width=self.virtual_width,
            height=self.virtual_height
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Force canvas to be fully initialized before binding events
        self.overlay.update_idletasks()
        
        # Draw instructions at the top (centered on virtual desktop)
        self.instruction_text = self.canvas.create_text(
            self.virtual_width // 2,
            40,
            text="Click and drag to select area • Press ESC to cancel",
            fill="white",
            font=("Arial", 14, "bold"),
            tags="instruction"
        )
        
        # Bind mouse events ONLY after canvas is fully initialized
        self.canvas.bind("<Button-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        self.overlay.bind("<Escape>", self.cancel_capture)
        
        # Set focus and ensure overlay is ready
        self.canvas.focus_set()
        self.overlay.update()
    
    def start_selection(self, event):
        """Start selection rectangle - using absolute screen coordinates"""
        # Safety check: ensure canvas is initialized
        if self.canvas is None:
            return
        
        # Hide instruction text when selection starts
        if hasattr(self, 'instruction_text') and self.instruction_text:
            try:
                self.canvas.itemconfig(self.instruction_text, state="hidden")
            except:
                pass
        
        # Store absolute screen coordinates (relative to virtual desktop origin)
        self.start_x_root = event.x_root
        self.start_y_root = event.y_root
        
        # Also store canvas coordinates for drawing (relative to overlay window)
        self.start_x = event.x
        self.start_y = event.y
        
        # Clear any existing selection
        if self.rect_id:
            try:
                self.canvas.delete(self.rect_id)
            except:
                pass
            self.rect_id = None
    
    def update_selection(self, event):
        """Update selection rectangle (rubber band) - native style with clear selection box"""
        # CRITICAL: Safety check to prevent NoneType errors
        if self.canvas is None:
            return
        
        # Delete previous rectangle if it exists
        if self.rect_id:
            try:
                self.canvas.delete(self.rect_id)
            except:
                pass
        
        # Calculate selection bounds - supports dragging in ANY direction
        # (top-left to bottom-right OR bottom-right to top-left, etc.)
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        # Native UX: Clear selection box (no dimming inside)
        # Draw a white rectangle that appears "clear" against the dimmed background
        # This creates the illusion of a clear selection area like native screenshot tools
        
        try:
            # Draw selection rectangle with white fill to appear clear (native screenshot tool style)
            self.rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="#2196F3",  # Solid blue border (bright blue)
                width=2,
                fill="",     # No fill — only border visible for clear selection
                tags="selection"
            )
            
            # Bring rectangle to front
            self.canvas.tag_raise(self.rect_id)
        except Exception as e:
            # Silently handle any drawing errors
            print(f"Error updating selection: {e}")
            self.rect_id = None
    
    def end_selection(self, event):
        """End selection and capture the area - using absolute screen coordinates"""
        # Safety check
        if self.canvas is None:
            self.hide()
            return
        
        # Use absolute screen coordinates (x_root, y_root) for capture
        end_x_root = event.x_root
        end_y_root = event.y_root
        
        # Calculate selection bounds in absolute screen coordinates
        # Supports dragging in any direction
        x1 = min(self.start_x_root, end_x_root)
        y1 = min(self.start_y_root, end_y_root)
        x2 = max(self.start_x_root, end_x_root)
        y2 = max(self.start_y_root, end_y_root)
        
        # Only capture if there's a meaningful selection
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            width = x2 - x1
            height = y2 - y1
            
            # Capture the selected area using absolute screen coordinates
            self.capture_area(x1, y1, width, height)
        else:
            self.hide()
    
    def capture_area(self, x, y, width, height):
        """Capture the selected screen area using MSS with absolute screen coordinates (multi-monitor aware)"""
        try:
            # Hide the overlay from the screen capture before taking the screenshot
            if self.overlay:
                try:
                    self.overlay.withdraw()
                    self.overlay.update()
                except:
                    pass
                # Small delay to ensure the window manager updates
                time.sleep(0.05)

            with mss.mss() as sct:
                # MSS uses absolute monitor coordinates (relative to virtual desktop)
                # The coordinates from x_root/y_root are already in the correct space
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                
                # Capture screenshot - MSS handles multi-monitor automatically
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Create captures directory if it doesn't exist
                captures_dir = "captures"
                if not os.path.exists(captures_dir):
                    os.makedirs(captures_dir)
                
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp}.png"
                output_path = os.path.join(captures_dir, filename)
                
                # Save the image
                img.save(output_path)
                
                # Destroy/hide overlay now that capture is done
                self.hide()
                
                # Call callback with the capture path
                if self.capture_callback:
                    self.capture_callback(output_path)
                    
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            import traceback
            traceback.print_exc()
            self.hide()
    
    def cancel_capture(self, event=None):
        """Cancel the capture overlay"""
        self.hide()
    
    def hide(self):
        """Hide the capture overlay"""
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
            self.canvas = None


class DeepfakeDetectorApp:
    """Main application window"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Deepfake Detection Utility")
        self.root.geometry("500x300")
        
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
        """Handle capture completion"""
        if os.path.exists(capture_path):
            filename = os.path.basename(capture_path)
            self.status_label.configure(
                text=f"Capture saved: {filename}",
                text_color="green"
            )
            # Here you can add your deepfake detection logic
            print(f"Capture saved to {capture_path}")
        else:
            self.status_label.configure(
                text="Capture failed",
                text_color="red"
            )
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if self.ask_button:
            self.ask_button.destroy()
        self.root.destroy()


if __name__ == "__main__":
    app = DeepfakeDetectorApp()
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()

