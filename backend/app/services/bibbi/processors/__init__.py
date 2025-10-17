"""
BIBBI Processors Package

Vendor-specific data processors for BIBBI resellers.

Each processor:
- Inherits from BibbiBseProcessor
- Handles vendor-specific Excel format
- Transforms to sales_unified schema
- Extracts store information
- Handles currency conversion
"""

from .base import BibbiBseProcessor, ProcessingResult
from .liberty_processor import LibertyProcessor, get_liberty_processor
from .galilu_processor import GaliluProcessor, get_galilu_processor
from .skins_sa_processor import SkinsSAProcessor, get_skins_sa_processor
from .boxnox_processor import BoxnoxProcessor, get_boxnox_processor
from .cdlc_processor import CDLCProcessor, get_cdlc_processor
from .aromateque_processor import AromatequProcessor, get_aromateque_processor
from .selfridges_processor import SelfridgesProcessor, get_selfridges_processor
from .skins_nl_processor import SkinsNLProcessor, get_skins_nl_processor

__all__ = [
    "BibbiBseProcessor",
    "ProcessingResult",
    "LibertyProcessor",
    "get_liberty_processor",
    "GaliluProcessor",
    "get_galilu_processor",
    "SkinsSAProcessor",
    "get_skins_sa_processor",
    "BoxnoxProcessor",
    "get_boxnox_processor",
    "CDLCProcessor",
    "get_cdlc_processor",
    "AromatequProcessor",
    "get_aromateque_processor",
    "SelfridgesProcessor",
    "get_selfridges_processor",
    "SkinsNLProcessor",
    "get_skins_nl_processor",
]
