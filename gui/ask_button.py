"""Draggable floating action button component"""

import customtkinter as ctk


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

