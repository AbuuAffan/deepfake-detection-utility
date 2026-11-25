"""Detector package for deepfake detection models"""

from .base import BaseDetector
from .hf_detector import HFDetector

__all__ = ['BaseDetector', 'HFDetector']

