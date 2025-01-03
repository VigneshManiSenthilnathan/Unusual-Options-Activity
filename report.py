import pandas as pd
import numpy as np
import yfinance as yf
from scipy import stats
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import json

from detector import OptionsDetector

class OptionsReport:
    def __init__(self, detector: OptionsDetector):
        self.detector = detector

    def generate_comprehensive_report(self):
        """Generate a comprehensive analysis report"""
        # Fetch and analyze all data
        historical_data = self.detector.get_historical_data()
        price_analysis = self.detector.analyze_price_movement(historical_data)
        options_data = self.detector.analyze_options_chain()
        
        # Calculate all metrics
        put_call_metrics = self.detector.calculate_put_call_ratio(options_data)
        flow_metrics = self.detector.track_options_flow(options_data)
        unusual_spreads = self.detector.detect_unusual_spreads(options_data)
        volatility_skew = self.detector.analyze_volatility_surface(options_data)
        
        # Compile report
        report = {
            'price_analysis': {
                'current_price': historical_data['Close'].iloc[-1],
                'daily_return': price_analysis['Returns'].iloc[-1],
                'historical_volatility': price_analysis['Historical_Volatility'].iloc[-1],
                '5_day_momentum': price_analysis['5_day_momentum'].iloc[-1],
                '20_day_momentum': price_analysis['20_day_momentum'].iloc[-1]
            },
            'options_metrics': {
                'put_call_ratios': put_call_metrics,
                'options_flow': flow_metrics,
                'unusual_spreads_count': len(unusual_spreads),
                'volatility_skew': volatility_skew
            }
        }
        
        return report

    def interpret_unusual_activity(self, report):
        """
        Provide plain English interpretation of the unusual options activity
        """
        interpretations = []
        alerts = []
        
        # Price Movement Analysis
        price_data = report['price_analysis']
        daily_return = price_data['daily_return'] * 100  # Convert to percentage
        
        if abs(daily_return) > 2:  # More than 2% daily move
            interpretations.append(
                f"Stock showed significant price movement today: {daily_return:.1f}% "
                f"{'increase' if daily_return > 0 else 'decrease'}"
            )
            if abs(daily_return) > 5:  # More than 5% move
                alerts.append("ALERT: Large price movement detected!")

        # Volatility Analysis
        hist_vol = price_data['historical_volatility'] * 100
        if hist_vol > 50:  # High volatility threshold
            interpretations.append(
                f"Historical volatility is elevated at {hist_vol:.1f}%, "
                "indicating increased market uncertainty"
            )

        # Options Flow Analysis
        flow = report['options_metrics']['options_flow']
        net_flow = flow['net_flow']
        flow_magnitude = abs(net_flow) / 1000000  # Convert to millions
        
        if flow_magnitude > 1:  # More than $1M net flow
            flow_direction = "bullish" if net_flow > 0 else "bearish"
            interpretations.append(
                f"Significant {flow_direction} options flow detected: "
                f"${flow_magnitude:.1f}M net {flow_direction} positions"
            )
            if flow_magnitude > 5:  # More than $5M net flow
                alerts.append(f"ALERT: Large {flow_direction} options flow detected!")

        # Put-Call Ratio Analysis
        pc_ratios = report['options_metrics']['put_call_ratios']
        volume_pc = pc_ratios['volume_put_call_ratio']
        
        if volume_pc > 1.5:
            interpretations.append(
                f"Elevated put-call ratio of {volume_pc:.2f} suggests bearish sentiment"
            )
            if volume_pc > 2.0:
                alerts.append("ALERT: Unusually high put volume detected!")
        elif volume_pc < 0.5:
            interpretations.append(
                f"Low put-call ratio of {volume_pc:.2f} suggests bullish sentiment"
            )
            if volume_pc < 0.3:
                alerts.append("ALERT: Unusually high call volume detected!")

        # Unusual Spreads Analysis
        unusual_spreads = report['options_metrics']['unusual_spreads_count']
        if unusual_spreads > 0:
            interpretations.append(
                f"Detected {unusual_spreads} options contracts with unusual bid-ask spreads"
            )
            if unusual_spreads > 5:
                alerts.append("ALERT: Multiple unusual options spreads detected!")

        return {
            'summary': self.generate_summary(interpretations, alerts),
            'detailed_interpretations': interpretations,
            'alerts': alerts
        }

    def generate_summary(self, interpretations, alerts):
        """
        Generate an overall summary of the unusual options activity
        """
        if not alerts and not interpretations:
            return "No significant unusual options activity detected at this time."
        
        alert_count = len(alerts)
        if alert_count > 2:
            severity = "HIGH"
        elif alert_count > 0:
            severity = "MEDIUM"
        else:
            severity = "LOW"
            
        return f"Unusual Activity Level: {severity}\n" + \
               f"Number of alerts: {alert_count}\n" + \
               "Key findings: " + "; ".join(interpretations[:3])  # Top 3 findings