"""
PanViTa Core Engine
Módulo principal contendo toda a lógica de análise pan-genômica
"""

from .config import PanViTaConfig
from .dependencies import DependencyManager
from .databases import DatabaseManager
from .downloader import NCBIDownloader
from .processor import GBKProcessor
from .aligner import Aligner
from .data_processor import DataProcessor
from .visualization import Visualization
from .file_handler import FileHandler
from .engine import PanViTaEngine

__version__ = "2.0.0"
__all__ = [
    'PanViTaConfig',
    'DependencyManager', 
    'DatabaseManager',
    'NCBIDownloader',
    'GBKProcessor',
    'Aligner',
    'DataProcessor',
    'Visualization',
    'PanViTaEngine',
    'FileHandler'
]
