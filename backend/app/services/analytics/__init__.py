"""
Analytics services for predictions and advanced analysis

This package provides:
- Time series forecasting (predictor.py)
- Trend and seasonality analysis (analyzer.py)
"""

from .predictor import SalesPredictionEngine
from .analyzer import SalesAnalysisEngine

__all__ = ['SalesPredictionEngine', 'SalesAnalysisEngine']
