"""Base detector interface"""

from abc import ABC, abstractmethod


class BaseDetector(ABC):
    """Abstract base class for deepfake detection models"""
    
    @abstractmethod
    def detect(self, file_path):
        """
        Detect if a file contains deepfake content.
        
        Args:
            file_path: Path to the image or video file to analyze
        
        Returns:
            dict: Detection result with keys:
                - is_fake (bool): True if deepfake detected, False otherwise
                - confidence (float): Confidence score between 0.0 and 1.0
                - model (str): Name/identifier of the model used
                - additional metadata (optional)
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        pass
    
    @abstractmethod
    def get_model_info(self):
        """
        Get information about the detection model.
        
        Returns:
            dict: Model information (name, version, capabilities, etc.)
        """
        pass

