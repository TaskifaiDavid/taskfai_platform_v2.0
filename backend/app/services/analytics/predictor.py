"""
Sales Prediction Engine - Time Series Forecasting

Provides multiple forecasting methods:
- Simple Moving Average (SMA)
- Linear Regression
- Exponential Smoothing  
- Seasonal Decomposition

All predictions include confidence intervals and validation.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import warnings

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Suppress statsmodels warnings
warnings.filterwarnings('ignore')


class SalesPredictionEngine:
    """
    Time series forecasting engine for sales predictions
    
    Features:
    - Multiple forecasting algorithms
    - Automatic method selection based on data characteristics
    - Confidence intervals for all predictions
    - Handles both daily (ecommerce) and monthly (sellout) data
    """
    
    MINIMUM_DATA_POINTS = 3  # Minimum historical data required
    DEFAULT_CONFIDENCE_LEVEL = 0.85  # 85% confidence interval
    
    def __init__(self, historical_data: List[Dict[str, Any]]):
        """
        Initialize prediction engine with historical sales data
        
        Args:
            historical_data: List of dicts with 'date' and 'sales' keys
                             [{'date': '2024-01-01', 'sales': 1234.56}, ...]
        """
        self.historical_data = historical_data
        self.df = self._prepare_data(historical_data)
        
    def _prepare_data(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert raw data to pandas DataFrame and prepare for analysis"""
        if not data:
            raise ValueError("No historical data provided")
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Ensure required columns
        if 'date' not in df.columns or 'sales' not in df.columns:
            raise ValueError("Data must contain 'date' and 'sales' columns")
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Convert sales to float
        df['sales'] = df['sales'].astype(float)
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Remove any rows with null sales
        df = df.dropna(subset=['sales'])
        
        return df
    
    def predict(
        self,
        target_date: date,
        method: str = 'auto',
        confidence_level: float = None
    ) -> Dict[str, Any]:
        """
        Generate sales prediction for target date
        
        Args:
            target_date: Date to predict sales for
            method: Forecasting method ('auto', 'sma', 'linear', 'exponential', 'seasonal')
            confidence_level: Confidence level for interval (default: 0.85)
            
        Returns:
            Dict with prediction, confidence intervals, and metadata
        """
        if len(self.df) < self.MINIMUM_DATA_POINTS:
            raise ValueError(
                f"Insufficient data: need at least {self.MINIMUM_DATA_POINTS} "
                f"historical points, got {len(self.df)}"
            )
        
        confidence_level = confidence_level or self.DEFAULT_CONFIDENCE_LEVEL
        
        # Select forecasting method
        if method == 'auto':
            method = self._select_best_method()
        
        # Generate prediction based on method
        if method == 'sma':
            prediction = self._predict_sma(target_date, confidence_level)
        elif method == 'linear':
            prediction = self._predict_linear(target_date, confidence_level)
        elif method == 'exponential':
            prediction = self._predict_exponential(target_date, confidence_level)
        elif method == 'seasonal':
            prediction = self._predict_seasonal(target_date, confidence_level)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Add metadata
        prediction['method'] = method
        prediction['confidence_level'] = confidence_level
        prediction['data_points_used'] = len(self.df)
        prediction['historical_period'] = {
            'start': self.df['date'].min().strftime('%Y-%m-%d'),
            'end': self.df['date'].max().strftime('%Y-%m-%d')
        }
        
        return prediction
    
    def predict_range(
        self,
        start_date: date,
        end_date: date,
        method: str = 'auto',
        confidence_level: float = None
    ) -> List[Dict[str, Any]]:
        """
        Generate predictions for date range
        
        Args:
            start_date: Start of prediction period
            end_date: End of prediction period  
            method: Forecasting method
            confidence_level: Confidence level for intervals
            
        Returns:
            List of predictions for each date in range
        """
        predictions = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                pred = self.predict(current_date, method, confidence_level)
                predictions.append(pred)
            except Exception as e:
                # Log error but continue with other dates
                print(f"Prediction failed for {current_date}: {e}")
            
            # Increment by 1 month (for monthly predictions)
            current_date = self._add_months(current_date, 1)
        
        return predictions
    
    def _select_best_method(self) -> str:
        """
        Automatically select best forecasting method based on data characteristics
        
        Returns:
            Method name ('sma', 'linear', 'exponential', 'seasonal')
        """
        n_points = len(self.df)
        
        # Check for seasonality
        if n_points >= 12:
            if self._has_seasonality():
                return 'seasonal'
        
        # Check for clear trend
        if n_points >= 6:
            trend_strength = self._calculate_trend_strength()
            if trend_strength > 0.7:
                return 'linear'
        
        # Check for exponential pattern (accelerating growth/decline)
        if n_points >= 4:
            if self._has_exponential_pattern():
                return 'exponential'
        
        # Default to simple moving average
        return 'sma'
    
    def _predict_sma(self, target_date: date, confidence_level: float) -> Dict[str, Any]:
        """Simple Moving Average prediction"""
        # Use last 3 months for moving average
        window = min(3, len(self.df))
        recent_sales = self.df['sales'].tail(window)
        
        prediction = recent_sales.mean()
        std_dev = recent_sales.std() if len(recent_sales) > 1 else 0
        
        # Calculate confidence interval
        margin = stats.norm.ppf((1 + confidence_level) / 2) * std_dev
        
        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'predicted_sales': round(float(prediction), 2),
            'confidence_interval': {
                'lower': round(float(max(0, prediction - margin)), 2),
                'upper': round(float(prediction + margin), 2)
            },
            'standard_deviation': round(float(std_dev), 2)
        }
    
    def _predict_linear(self, target_date: date, confidence_level: float) -> Dict[str, Any]:
        """Linear regression prediction"""
        # Prepare features (days since first date)
        base_date = self.df['date'].min()
        X = np.array([(d - base_date).days for d in self.df['date']]).reshape(-1, 1)
        y = self.df['sales'].values
        
        # Fit linear model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict for target date
        target_days = (pd.Timestamp(target_date) - base_date).days
        prediction = model.predict([[target_days]])[0]
        
        # Calculate prediction interval using residuals
        residuals = y - model.predict(X)
        residual_std = np.std(residuals)
        margin = stats.norm.ppf((1 + confidence_level) / 2) * residual_std
        
        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'predicted_sales': round(float(prediction), 2),
            'confidence_interval': {
                'lower': round(float(max(0, prediction - margin)), 2),
                'upper': round(float(prediction + margin), 2)
            },
            'trend_coefficient': round(float(model.coef_[0]), 4),
            'r_squared': round(float(model.score(X, y)), 3)
        }
    
    def _predict_exponential(self, target_date: date, confidence_level: float) -> Dict[str, Any]:
        """Exponential smoothing prediction"""
        sales = self.df['sales'].values
        
        # Simple exponential smoothing with alpha=0.3
        alpha = 0.3
        smoothed = [sales[0]]
        for i in range(1, len(sales)):
            smoothed.append(alpha * sales[i] + (1 - alpha) * smoothed[i-1])
        
        prediction = smoothed[-1]
        
        # Calculate error margin
        errors = sales[1:] - smoothed[:-1]
        error_std = np.std(errors) if len(errors) > 0 else 0
        margin = stats.norm.ppf((1 + confidence_level) / 2) * error_std
        
        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'predicted_sales': round(float(prediction), 2),
            'confidence_interval': {
                'lower': round(float(max(0, prediction - margin)), 2),
                'upper': round(float(prediction + margin), 2)
            },
            'smoothing_factor': alpha
        }
    
    def _predict_seasonal(self, target_date: date, confidence_level: float) -> Dict[str, Any]:
        """Seasonal decomposition prediction"""
        if len(self.df) < 12:
            # Not enough data for seasonal analysis, fall back to linear
            return self._predict_linear(target_date, confidence_level)
        
        # Extract month from target date
        target_month = target_date.month
        
        # Calculate average sales for each month
        self.df['month'] = self.df['date'].dt.month
        monthly_avg = self.df.groupby('month')['sales'].mean()
        
        # Calculate overall trend
        base_date = self.df['date'].min()
        X = np.array([(d - base_date).days for d in self.df['date']]).reshape(-1, 1)
        y = self.df['sales'].values
        
        trend_model = LinearRegression()
        trend_model.fit(X, y)
        
        # Predict trend for target date
        target_days = (pd.Timestamp(target_date) - base_date).days
        trend_prediction = trend_model.predict([[target_days]])[0]
        
        # Apply seasonal factor
        overall_avg = self.df['sales'].mean()
        seasonal_factor = monthly_avg.get(target_month, 1.0) / overall_avg
        prediction = trend_prediction * seasonal_factor
        
        # Calculate confidence interval
        residuals = y - trend_model.predict(X)
        residual_std = np.std(residuals)
        margin = stats.norm.ppf((1 + confidence_level) / 2) * residual_std * seasonal_factor
        
        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'predicted_sales': round(float(prediction), 2),
            'confidence_interval': {
                'lower': round(float(max(0, prediction - margin)), 2),
                'upper': round(float(prediction + margin), 2)
            },
            'seasonal_factor': round(float(seasonal_factor), 3),
            'trend_component': round(float(trend_prediction), 2)
        }
    
    def _has_seasonality(self) -> bool:
        """Detect if data shows seasonal patterns"""
        if len(self.df) < 12:
            return False
        
        # Simple seasonality check: compare variance within months vs between months
        self.df['month'] = self.df['date'].dt.month
        monthly_groups = self.df.groupby('month')['sales'].mean()
        
        if len(monthly_groups) < 4:
            return False
        
        # If variance between months is significantly higher than random, likely seasonal
        between_month_variance = monthly_groups.var()
        total_variance = self.df['sales'].var()
        
        return between_month_variance / total_variance > 0.3
    
    def _calculate_trend_strength(self) -> float:
        """Calculate strength of linear trend (R-squared)"""
        base_date = self.df['date'].min()
        X = np.array([(d - base_date).days for d in self.df['date']]).reshape(-1, 1)
        y = self.df['sales'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        return model.score(X, y)
    
    def _has_exponential_pattern(self) -> bool:
        """Detect exponential growth/decline pattern"""
        if len(self.df) < 4:
            return False
        
        # Calculate period-over-period growth rates
        sales = self.df['sales'].values
        growth_rates = []
        for i in range(1, len(sales)):
            if sales[i-1] > 0:
                growth = (sales[i] - sales[i-1]) / sales[i-1]
                growth_rates.append(growth)
        
        if not growth_rates:
            return False
        
        # Exponential pattern: growth rates should be relatively consistent
        growth_std = np.std(growth_rates)
        growth_mean = np.abs(np.mean(growth_rates))
        
        # If consistent growth (low variance) and significant rate
        return growth_std < 0.2 and growth_mean > 0.05
    
    @staticmethod
    def _add_months(source_date: date, months: int) -> date:
        """Add months to date, handling month overflow"""
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        return date(year, month, day)
    
    def get_forecast_summary(
        self,
        target_date: date,
        methods: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get predictions from multiple methods for comparison
        
        Args:
            target_date: Date to predict
            methods: List of methods to try (default: all applicable)
            
        Returns:
            Dict with predictions from each method
        """
        if methods is None:
            methods = ['sma', 'linear', 'exponential']
            if len(self.df) >= 12:
                methods.append('seasonal')
        
        results = {}
        for method in methods:
            try:
                results[method] = self.predict(target_date, method=method)
            except Exception as e:
                results[method] = {'error': str(e)}
        
        # Add consensus prediction (average of valid predictions)
        valid_predictions = [
            r['predicted_sales'] for r in results.values()
            if 'predicted_sales' in r
        ]
        if valid_predictions:
            results['consensus'] = {
                'predicted_sales': round(np.mean(valid_predictions), 2),
                'methods_used': len(valid_predictions),
                'range': {
                    'min': round(min(valid_predictions), 2),
                    'max': round(max(valid_predictions), 2)
                }
            }
        
        return results


# Helper function for creating predictions from raw Supabase data
def create_prediction_from_supabase_data(
    supabase_data: List[Dict[str, Any]],
    target_date: date,
    method: str = 'auto'
) -> Dict[str, Any]:
    """
    Create prediction from Supabase query results
    
    Args:
        supabase_data: Results from ecommerce_orders or sellout_entries2 query
        target_date: Date to predict for
        method: Forecasting method
        
    Returns:
        Prediction dictionary
    """
    # Convert Supabase data to standard format
    historical_data = []
    
    for record in supabase_data:
        # Handle both ecommerce_orders (order_date) and sellout_entries2 (month/year)
        if 'order_date' in record:
            date_str = record['order_date']
        elif 'year' in record and 'month' in record:
            date_str = f"{record['year']}-{record['month']:02d}-01"
        else:
            continue
        
        sales = float(record.get('sales_eur', 0) or 0)
        
        historical_data.append({
            'date': date_str,
            'sales': sales
        })
    
    # Create engine and predict
    engine = SalesPredictionEngine(historical_data)
    return engine.predict(target_date, method=method)
