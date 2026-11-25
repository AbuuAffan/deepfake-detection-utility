"""Capture engine for screen and media capture"""

import mss
from PIL import Image
import os
from datetime import datetime
import time


class CaptureEngine:
    """Engine for capturing screen areas and media (images now, video later)"""
    
    def __init__(self, output_dir="captures"):
        """
        Initialize the capture engine.
        
        Args:
            output_dir: Directory to save captures (default: "captures")
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure the output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def get_monitor_geometry(self):
        """
        Get all monitor geometries and calculate virtual desktop bounding box.
        
        Returns:
            tuple: (monitors_list, (left, top, width, height))
        """
        with mss.mss() as sct:
            # Get all monitors - monitor 0 is the combined virtual desktop
            all_monitors = sct.monitors
            
            if len(all_monitors) > 1:
                # Multiple monitors detected - use individual monitors
                monitors = all_monitors[1:]  # Skip monitor 0 (all monitors combined)
            else:
                # Single monitor - use monitor 0
                monitors = [all_monitors[0]]
            
            # Calculate virtual desktop bounding box
            lefts = [m['left'] for m in monitors]
            tops = [m['top'] for m in monitors]
            rights = [m['left'] + m['width'] for m in monitors]
            bottoms = [m['top'] + m['height'] for m in monitors]
            
            virtual_left = min(lefts)
            virtual_top = min(tops)
            virtual_width = max(rights) - virtual_left
            virtual_height = max(bottoms) - virtual_top
            
            return monitors, (virtual_left, virtual_top, virtual_width, virtual_height)
    
    def capture_screen_area(self, x, y, width, height, delay=0.05):
        """
        Capture a specific screen area.
        
        Args:
            x: Left coordinate (absolute screen position)
            y: Top coordinate (absolute screen position)
            width: Width of the area to capture
            height: Height of the area to capture
            delay: Delay before capture to ensure window manager updates (default: 0.05s)
        
        Returns:
            str: Path to the saved image file, or None if capture failed
        """
        try:
            # Small delay to ensure the window manager updates
            time.sleep(delay)
            
            with mss.mss() as sct:
                # MSS uses absolute monitor coordinates (relative to virtual desktop)
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                
                # Capture screenshot - MSS handles multi-monitor automatically
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp}.png"
                output_path = os.path.join(self.output_dir, filename)
                
                # Save the image
                img.save(output_path)
                
                return output_path
                
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def capture_image(self, image_path):
        """
        Capture/process an image file (for future use with file uploads).
        
        Args:
            image_path: Path to the image file
        
        Returns:
            str: Path to the processed/saved image, or None if failed
        """
        # Placeholder for future image processing
        # This can be used when users upload images directly
        if os.path.exists(image_path):
            return image_path
        return None
    
    def capture_video(self, video_path):
        """
        Capture/process a video file (for future implementation).
        
        Args:
            video_path: Path to the video file
        
        Returns:
            str: Path to the processed video, or None if failed
        """
        # Placeholder for future video capture/processing
        # This will be implemented when video support is added
        raise NotImplementedError("Video capture not yet implemented")

