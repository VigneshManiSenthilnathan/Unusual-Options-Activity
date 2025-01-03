import pandas as pd
import numpy as np
import yfinance as yf
from scipy import stats
from datetime import datetime, timedelta
from dynamicThreshold import DynamicThresholdCalculator

class OptionsDetector:
    def __init__(self, symbol, lookback_period=252):
        self.symbol = symbol
        self.lookback_period = lookback_period
        self.thresholds = {}
        self.stock = yf.Ticker(symbol)

    def initialize_dynamic_thresholds(self):
        """
        Initialize dynamic thresholds based on current market conditions
        """
        historical_data = self.get_historical_data()
        options_data = self.analyze_options_chain()
        
        threshold_calculator = DynamicThresholdCalculator(historical_data, options_data)
        
        # Get both volatility and liquidity based thresholds
        vol_thresholds = threshold_calculator.calculate_volatility_based_threshold()
        liq_thresholds = threshold_calculator.calculate_liquidity_based_threshold()
        
        # Combine thresholds
        self.thresholds = {
            'price_move': vol_thresholds['price_move_threshold'],
            'volume': vol_thresholds['volume_threshold'] * liq_thresholds['volume_multiplier'],
            'iv': vol_thresholds['iv_threshold'],
            'spread': liq_thresholds['spread_threshold'],
            'oi': liq_thresholds['oi_threshold']
        }
        
        return self.thresholds
        
    def get_historical_data(self):
        """Fetch historical price data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_period)
        
        historical_data = self.stock.history(
            start=start_date,
            end=end_date,
            interval='1d'
        )
        return historical_data

    def analyze_price_movement(self, historical_data):
        """Analyze price movements and volatility"""
        historical_data['Returns'] = historical_data['Close'].pct_change()
        historical_data['Historical_Volatility'] = (
            historical_data['Returns'].rolling(window=20).std() * np.sqrt(252)
        )
        
        # Calculate price momentum
        historical_data['5_day_momentum'] = historical_data['Close'].pct_change(periods=5)
        historical_data['20_day_momentum'] = historical_data['Close'].pct_change(periods=20)
        
        return historical_data

    def analyze_options_chain(self):
        """Enhanced options chain analysis"""
        all_options = []
        expirations = self.stock.options

        for exp in expirations:
            opt = self.stock.option_chain(exp)
            
            # Enhance calls data
            calls = opt.calls
            calls['type'] = 'call'
            calls['expiration'] = exp
            
            # Enhance puts data
            puts = opt.puts
            puts['type'] = 'put'
            puts['expiration'] = exp
            
            # Calculate spread metrics
            calls['bid_ask_spread'] = calls['ask'] - calls['bid']
            calls['spread_percentage'] = calls['bid_ask_spread'] / calls['ask'] * 100
            puts['bid_ask_spread'] = puts['ask'] - puts['bid']
            puts['spread_percentage'] = puts['spread_percentage'] = puts['bid_ask_spread'] / puts['ask'] * 100
            
            chain = pd.concat([calls, puts])
            all_options.append(chain)
            
        return pd.concat(all_options)

    def calculate_put_call_ratio(self, options_data):
        """Calculate put-call ratio metrics"""
        call_volume = options_data[options_data['type'] == 'call']['volume'].sum()
        put_volume = options_data[options_data['type'] == 'put']['volume'].sum()
        
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        call_oi = options_data[options_data['type'] == 'call']['openInterest'].sum()
        put_oi = options_data[options_data['type'] == 'put']['openInterest'].sum()
        
        put_call_oi_ratio = put_oi / call_oi if call_oi > 0 else 0
        
        return {
            'volume_put_call_ratio': put_call_ratio,
            'oi_put_call_ratio': put_call_oi_ratio
        }

    def track_options_flow(self, options_data):
        """
        Track and analyze options flow using dynamic thresholds
        """
        if not self.thresholds:
            self.initialize_dynamic_thresholds()
        
        options_data['dollar_volume'] = options_data['volume'] * options_data['lastPrice'] * 100
        
        # Define dynamic thresholds for flow separation
        volume_threshold = self.thresholds['volume']
        
        # Separate bullish and bearish flow
        bullish_flow = options_data[
            ((options_data['type'] == 'call') & (options_data['lastPrice'] > options_data['bid'])) |
            ((options_data['type'] == 'put') & (options_data['lastPrice'] < options_data['ask']))
        ]
        bearish_flow = options_data[
            ((options_data['type'] == 'put') & (options_data['lastPrice'] > options_data['bid'])) |
            ((options_data['type'] == 'call') & (options_data['lastPrice'] < options_data['ask']))
        ]
        
        return {
            'bullish_flow': bullish_flow['dollar_volume'].sum(),
            'bearish_flow': bearish_flow['dollar_volume'].sum(),
            'net_flow': bullish_flow['dollar_volume'].sum() - bearish_flow['dollar_volume'].sum()
        }

    def detect_unusual_spreads(self, options_data):
        """
        Detect unusual options spreads based on dynamic thresholds
        """
        if not self.thresholds:
            self.initialize_dynamic_thresholds()
        
        # Calculate z-scores for spread metrics
        options_data['spread_z_score'] = stats.zscore(options_data['spread_percentage'])
        
        # Identify unusual spreads using dynamic thresholds
        unusual_spreads = options_data[
            (options_data['spread_z_score'] > self.thresholds['spread']) & 
            (options_data['volume'] > self.thresholds['volume'])
        ]
        
        return unusual_spreads

    def analyze_volatility_surface(self, options_data):
        """Analyze the volatility surface for anomalies"""
        pivot_iv = pd.pivot_table(
            options_data,
            values='impliedVolatility',
            index='strike',
            columns='expiration'
        )
        
        # Calculate volatility skew
        atm_strike = self.stock.info["currentPrice"]
        closest_strikes = np.abs(pivot_iv.index - atm_strike).argsort()[:2]
        
        volatility_skew = {
            exp: pivot_iv[exp].iloc[closest_strikes].mean() 
            for exp in pivot_iv.columns
        }
        
        return volatility_skew