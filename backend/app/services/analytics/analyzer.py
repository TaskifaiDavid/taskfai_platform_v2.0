"""
Sales Analysis Engine - Advanced Statistical Analysis

Provides comprehensive sales analytics:
- Trend analysis (MoM, YoY growth rates)
- Seasonality detection and quantification
- Anomaly detection
- Comparative period analysis
- Product performance metrics
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict
import warnings

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression

warnings.filterwarnings('ignore')


class SalesAnalysisEngine:
    """
    Advanced statistical analysis engine for sales data
    
    Features:
    - Trend analysis with growth rates
    - Seasonality detection and patterns
    - Anomaly identification
    - Period comparisons
    - Performance benchmarking
    """
    
    def __init__(self, historical_data: List[Dict[str, Any]]):
        """
        Initialize analysis engine with historical data
        
        Args:
            historical_data: List of dicts with 'date' and 'sales' keys
        """
        self.historical_data = historical_data
        self.df = self._prepare_data(historical_data)
    
    def _prepare_data(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert raw data to pandas DataFrame"""
        if not data:
            raise ValueError("No historical data provided")
        
        df = pd.DataFrame(data)
        
        if 'date' not in df.columns or 'sales' not in df.columns:
            raise ValueError("Data must contain 'date' and 'sales' columns")
        
        df['date'] = pd.to_datetime(df['date'])
        df['sales'] = df['sales'].astype(float)
        df = df.sort_values('date').reset_index(drop=True)
        df = df.dropna(subset=['sales'])
        
        # Add time-based features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_week'] = df['date'].dt.dayofweek
        
        return df
    
    def analyze_trends(self, period: str = 'month') -> Dict[str, Any]:
        """
        Analyze sales trends over time
        
        Args:
            period: Aggregation period ('day', 'week', 'month', 'quarter')
            
        Returns:
            Dict with trend metrics (growth rates, acceleration, direction)
        """
        if len(self.df) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        # Aggregate by period
        if period == 'month':
            aggregated = self.df.groupby(['year', 'month'])['sales'].sum().reset_index()
            aggregated['period'] = pd.to_datetime(
                aggregated['year'].astype(str) + '-' + 
                aggregated['month'].astype(str) + '-01'
            )
        elif period == 'quarter':
            aggregated = self.df.groupby(['year', 'quarter'])['sales'].sum().reset_index()
            aggregated['period'] = pd.PeriodIndex(
                year=aggregated['year'], 
                quarter=aggregated['quarter'], 
                freq='Q'
            ).to_timestamp()
        else:
            aggregated = self.df[['date', 'sales']].copy()
            aggregated['period'] = aggregated['date']
        
        aggregated = aggregated.sort_values('period').reset_index(drop=True)
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(aggregated)):
            prev_sales = aggregated.iloc[i-1]['sales']
            curr_sales = aggregated.iloc[i]['sales']
            if prev_sales > 0:
                growth = ((curr_sales - prev_sales) / prev_sales) * 100
                growth_rates.append(growth)
        
        # Calculate trend metrics
        if len(aggregated) >= 2:
            # Linear regression for overall trend
            X = np.arange(len(aggregated)).reshape(-1, 1)
            y = aggregated['sales'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            trend_coefficient = model.coef_[0]
            trend_direction = 'increasing' if trend_coefficient > 0 else 'decreasing'
            r_squared = model.score(X, y)
        else:
            trend_coefficient = 0
            trend_direction = 'stable'
            r_squared = 0
        
        # Calculate acceleration (change in growth rate)
        acceleration = None
        if len(growth_rates) >= 2:
            recent_growth = np.mean(growth_rates[-3:]) if len(growth_rates) >= 3 else growth_rates[-1]
            earlier_growth = np.mean(growth_rates[:3]) if len(growth_rates) >= 3 else growth_rates[0]
            acceleration = recent_growth - earlier_growth
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': round(abs(trend_coefficient), 2),
            'r_squared': round(r_squared, 3),
            'average_growth_rate': round(np.mean(growth_rates), 2) if growth_rates else None,
            'latest_growth_rate': round(growth_rates[-1], 2) if growth_rates else None,
            'acceleration': round(acceleration, 2) if acceleration is not None else None,
            'periods_analyzed': len(aggregated),
            'period_type': period,
            'total_sales': round(aggregated['sales'].sum(), 2),
            'average_period_sales': round(aggregated['sales'].mean(), 2),
            'peak_period': {
                'date': aggregated.loc[aggregated['sales'].idxmax()]['period'].strftime('%Y-%m-%d'),
                'sales': round(aggregated['sales'].max(), 2)
            },
            'lowest_period': {
                'date': aggregated.loc[aggregated['sales'].idxmin()]['period'].strftime('%Y-%m-%d'),
                'sales': round(aggregated['sales'].min(), 2)
            }
        }
    
    def detect_seasonality(self) -> Dict[str, Any]:
        """
        Detect and quantify seasonal patterns in sales data
        
        Returns:
            Dict with seasonality metrics and patterns
        """
        if len(self.df) < 12:
            return {
                'has_seasonality': False,
                'message': 'Need at least 12 months of data for seasonality analysis'
            }
        
        # Monthly seasonality analysis
        monthly_avg = self.df.groupby('month')['sales'].mean()
        overall_avg = self.df['sales'].mean()
        
        # Calculate seasonal indices (ratio to overall average)
        seasonal_indices = (monthly_avg / overall_avg).to_dict()
        
        # Calculate seasonality strength (coefficient of variation)
        seasonality_strength = monthly_avg.std() / monthly_avg.mean() if monthly_avg.mean() > 0 else 0
        
        # Identify peak and low seasons
        peak_months = monthly_avg.nlargest(3).index.tolist()
        low_months = monthly_avg.nsmallest(3).index.tolist()
        
        # Statistical test for seasonality (one-way ANOVA)
        month_groups = [group['sales'].values for _, group in self.df.groupby('month')]
        f_stat, p_value = stats.f_oneway(*month_groups)
        has_significant_seasonality = p_value < 0.05
        
        return {
            'has_seasonality': has_significant_seasonality,
            'seasonality_strength': round(seasonality_strength, 3),
            'p_value': round(p_value, 4),
            'seasonal_indices': {
                int(month): round(index, 3) 
                for month, index in seasonal_indices.items()
            },
            'peak_months': [int(m) for m in peak_months],
            'low_months': [int(m) for m in low_months],
            'peak_month_multiplier': round(max(seasonal_indices.values()), 2),
            'low_month_multiplier': round(min(seasonal_indices.values()), 2),
            'month_names': {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
        }
    
    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalies (unusual spikes or drops) in sales data
        
        Args:
            threshold: Number of standard deviations for anomaly detection
            
        Returns:
            List of anomalous periods with details
        """
        if len(self.df) < 5:
            return []
        
        # Calculate z-scores
        mean_sales = self.df['sales'].mean()
        std_sales = self.df['sales'].std()
        
        if std_sales == 0:
            return []
        
        self.df['z_score'] = (self.df['sales'] - mean_sales) / std_sales
        
        # Identify anomalies
        anomalies = self.df[abs(self.df['z_score']) > threshold].copy()
        
        anomaly_list = []
        for _, row in anomalies.iterrows():
            anomaly_type = 'spike' if row['z_score'] > 0 else 'drop'
            severity = 'high' if abs(row['z_score']) > 3 else 'moderate'
            
            anomaly_list.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'sales': round(row['sales'], 2),
                'z_score': round(row['z_score'], 2),
                'type': anomaly_type,
                'severity': severity,
                'deviation_from_mean': round(row['sales'] - mean_sales, 2),
                'percent_deviation': round(((row['sales'] - mean_sales) / mean_sales) * 100, 1)
            })
        
        return sorted(anomaly_list, key=lambda x: abs(x['z_score']), reverse=True)
    
    def compare_periods(
        self,
        period1_start: date,
        period1_end: date,
        period2_start: date,
        period2_end: date
    ) -> Dict[str, Any]:
        """
        Compare sales between two time periods
        
        Args:
            period1_start: Start of first period
            period1_end: End of first period
            period2_start: Start of second period
            period2_end: End of second period
            
        Returns:
            Dict with comparison metrics
        """
        # Filter data for each period
        period1_data = self.df[
            (self.df['date'] >= pd.Timestamp(period1_start)) &
            (self.df['date'] <= pd.Timestamp(period1_end))
        ]
        
        period2_data = self.df[
            (self.df['date'] >= pd.Timestamp(period2_start)) &
            (self.df['date'] <= pd.Timestamp(period2_end))
        ]
        
        if len(period1_data) == 0 or len(period2_data) == 0:
            return {'error': 'No data found for one or both periods'}
        
        # Calculate metrics for each period
        period1_sales = period1_data['sales'].sum()
        period2_sales = period2_data['sales'].sum()
        
        period1_avg = period1_data['sales'].mean()
        period2_avg = period2_data['sales'].mean()
        
        # Calculate changes
        absolute_change = period2_sales - period1_sales
        percent_change = ((period2_sales - period1_sales) / period1_sales * 100) if period1_sales > 0 else 0
        
        avg_change = ((period2_avg - period1_avg) / period1_avg * 100) if period1_avg > 0 else 0
        
        return {
            'period1': {
                'start': period1_start.strftime('%Y-%m-%d'),
                'end': period1_end.strftime('%Y-%m-%d'),
                'total_sales': round(period1_sales, 2),
                'average_daily_sales': round(period1_avg, 2),
                'days': len(period1_data)
            },
            'period2': {
                'start': period2_start.strftime('%Y-%m-%d'),
                'end': period2_end.strftime('%Y-%m-%d'),
                'total_sales': round(period2_sales, 2),
                'average_daily_sales': round(period2_avg, 2),
                'days': len(period2_data)
            },
            'comparison': {
                'absolute_change': round(absolute_change, 2),
                'percent_change': round(percent_change, 2),
                'average_change_percent': round(avg_change, 2),
                'trend': 'growth' if percent_change > 0 else 'decline' if percent_change < 0 else 'stable'
            }
        }
    
    def analyze_velocity(self, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Analyze sales velocity (rate of change) over recent period
        
        Args:
            lookback_days: Number of recent days to analyze
            
        Returns:
            Dict with velocity metrics
        """
        if len(self.df) < 2:
            return {'error': 'Insufficient data for velocity analysis'}
        
        # Get recent data
        cutoff_date = self.df['date'].max() - pd.Timedelta(days=lookback_days)
        recent_data = self.df[self.df['date'] >= cutoff_date].copy()
        
        if len(recent_data) < 2:
            return {'error': f'No data in last {lookback_days} days'}
        
        # Calculate daily velocity
        recent_data['days_since_start'] = (recent_data['date'] - recent_data['date'].min()).dt.days
        
        # Linear regression on recent data
        X = recent_data['days_since_start'].values.reshape(-1, 1)
        y = recent_data['sales'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        velocity = model.coef_[0]  # Sales per day
        
        return {
            'velocity_per_day': round(velocity, 2),
            'projected_monthly': round(velocity * 30, 2),
            'trend': 'accelerating' if velocity > 0 else 'decelerating',
            'lookback_period_days': lookback_days,
            'data_points': len(recent_data),
            'period_start': recent_data['date'].min().strftime('%Y-%m-%d'),
            'period_end': recent_data['date'].max().strftime('%Y-%m-%d')
        }
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report
        
        Returns:
            Dict with all analysis metrics
        """
        return {
            'trends': self.analyze_trends(period='month'),
            'seasonality': self.detect_seasonality(),
            'anomalies': self.detect_anomalies(),
            'velocity': self.analyze_velocity(lookback_days=30),
            'data_summary': {
                'total_data_points': len(self.df),
                'date_range': {
                    'start': self.df['date'].min().strftime('%Y-%m-%d'),
                    'end': self.df['date'].max().strftime('%Y-%m-%d')
                },
                'total_sales': round(self.df['sales'].sum(), 2),
                'average_sales': round(self.df['sales'].mean(), 2),
                'median_sales': round(self.df['sales'].median(), 2)
            }
        }


# Helper function for creating analysis from Supabase data
def analyze_supabase_data(supabase_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze Supabase query results
    
    Args:
        supabase_data: Results from ecommerce_orders or sellout_entries2 query
        
    Returns:
        Comprehensive analysis dictionary
    """
    # Convert Supabase data to standard format
    historical_data = []
    
    for record in supabase_data:
        # Handle both data formats
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
    
    # Create engine and analyze
    engine = SalesAnalysisEngine(historical_data)
    return engine.get_comprehensive_analysis()
