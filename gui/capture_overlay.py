"""Screen capture overlay component"""

import tkinter as tk
from capture.engine import CaptureEngine


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
        self.capture_engine = CaptureEngine()
        
    def get_multi_monitor_geometry(self):
        """Detect all monitors and calculate virtual desktop bounding box"""
        self.monitors, (self.virtual_left, self.virtual_top, 
                       self.virtual_width, self.virtual_height) = self.capture_engine.get_monitor_geometry()
    
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
        """Capture the selected screen area using CaptureEngine"""
        try:
            # Hide the overlay from the screen capture before taking the screenshot
            if self.overlay:
                try:
                    self.overlay.withdraw()
                    self.overlay.update()
                except:
                    pass
            
            # Use CaptureEngine to capture the area
            output_path = self.capture_engine.capture_screen_area(x, y, width, height)
            
            # Destroy/hide overlay now that capture is done
            self.hide()
            
            # Call callback with the capture path
            if self.capture_callback and output_path:
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

