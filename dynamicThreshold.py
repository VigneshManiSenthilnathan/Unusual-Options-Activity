import pandas as pd
import numpy as np
import yfinance as yf
from scipy import stats
from datetime import datetime, timedelta

class DynamicThresholdCalculator:
    """
    Separate class to handle dynamic threshold calculations
    """
    def __init__(self, historical_data, options_data):
        self.historical_data = historical_data
        self.options_data = options_data
        
    def calculate_volatility_based_threshold(self, lookback=252):
        """
        Calculate dynamic thresholds based on historical volatility
        """
        # Calculate daily returns and rolling volatility
        returns = self.historical_data['Close'].pct_change()
        rolling_vol = returns.rolling(window=20).std() * np.sqrt(252)
        
        # Calculate volatility regime
        vol_percentile = rolling_vol.rank(pct=True).iloc[-1]
        
        # Adjust thresholds based on volatility regime
        if vol_percentile > 0.8:  # High volatility regime
            return {
                'price_move_threshold': rolling_vol.iloc[-1] * 0.5,  # Half daily vol
                'volume_threshold': 2.5,  # More sensitive in high vol
                'iv_threshold': 1.8
            }
        elif vol_percentile < 0.2:  # Low volatility regime
            return {
                'price_move_threshold': rolling_vol.iloc[-1] * 1.5,  # 1.5x daily vol
                'volume_threshold': 4.0,  # Less sensitive in low vol
                'iv_threshold': 2.5
            }
        else:  # Medium volatility regime
            return {
                'price_move_threshold': rolling_vol.iloc[-1] * 1.0,  # 1x daily vol
                'volume_threshold': 3.0,
                'iv_threshold': 2.0
            }

    def calculate_liquidity_based_threshold(self):
        """
        Calculate dynamic thresholds based on options liquidity
        """
        # Calculate median bid-ask spreads and volumes
        self.options_data['relative_spread'] = (
            (self.options_data['ask'] - self.options_data['bid']) / 
            ((self.options_data['ask'] + self.options_data['bid']) / 2)
        )
        
        median_spread = self.options_data['relative_spread'].median()
        median_volume = self.options_data['volume'].median()
        
        # Classify liquidity regime
        if median_spread > 0.05 or median_volume < 100:  # Low liquidity
            return {
                'spread_threshold': 3.0,  # Less sensitive to spread changes
                'volume_multiplier': 2.0,  # More sensitive to volume spikes
                'oi_threshold': 1.5
            }
        elif median_spread < 0.02 and median_volume > 1000:  # High liquidity
            return {
                'spread_threshold': 5.0,  # More sensitive to spread changes
                'volume_multiplier': 4.0,  # Less sensitive to volume spikes
                'oi_threshold': 2.5
            }
        else:  # Medium liquidity
            return {
                'spread_threshold': 4.0,
                'volume_multiplier': 3.0,
                'oi_threshold': 2.0
            }
