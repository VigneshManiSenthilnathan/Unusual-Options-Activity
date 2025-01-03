import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

from detector import OptionsDetector
from report import OptionsReport

def visualize_analysis(self):
    """Create visualizations for the analysis"""
    options_data = self.detector.analyze_options_chain()
    options_data = options_data.reset_index(drop=True)
    options_data = options_data.dropna(subset=['type', 'volume'])
    options_data['volume'] = options_data['volume'].fillna(0)
    options_data['volume'] = pd.to_numeric(options_data['volume'], errors='coerce')

    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Volume Distribution
    sns.boxplot(x='type', y='volume', data=options_data, ax=axes[0,0])
    axes[0,0].set_title('Options Volume Distribution by Type')
    
    # Plot 2: Implied Volatility Surface
    pivot_iv = pd.pivot_table(
        options_data,
        values='impliedVolatility',
        index='strike',
        columns='expiration'
    )
    sns.heatmap(pivot_iv, ax=axes[0,1])
    axes[0,1].set_title('Implied Volatility Surface')
    
    # Plot 3: Bid-Ask Spread Distribution
    sns.histplot(options_data['spread_percentage'], ax=axes[1,0])
    axes[1,0].set_title('Bid-Ask Spread Distribution')
    
    # Plot 4: Options Flow
    flow_data = self.track_options_flow(options_data)
    axes[1,1].bar(['Bullish Flow', 'Bearish Flow'], 
                    [flow_data['bullish_flow'], flow_data['bearish_flow']])
    axes[1,1].set_title('Options Flow Analysis')
    
    plt.tight_layout()
    return fig

def generate_readable_report(ticker: str, report_obj: OptionsReport):
    """
    Generate a human-readable report of the unusual options activity
    """
    report = report_obj.generate_comprehensive_report()
    interpretation = report_obj.interpret_unusual_activity(report)
    
    print("\n" + "="*50)
    print(f"OPTIONS ACTIVITY REPORT FOR {ticker}")
    print("="*50)
    
    print("\nSUMMARY:")
    print("-"*50)
    print(interpretation['summary'])
    
    if interpretation['alerts']:
        print("\nALERTS:")
        print("-"*50)
        for alert in interpretation['alerts']:
            print(f"⚠️ {alert}")
    
    print("\nDETAILED ANALYSIS:")
    print("-"*50)
    for i, interpretation in enumerate(interpretation['detailed_interpretations'], 1):
        print(f"{i}. {interpretation}")
    
    return interpretation

def main():
    ticker = "AMZN"
    detector = OptionsDetector(ticker)
    report = OptionsReport(detector)
    
    # Generate a comprehensive report
    comprehensive_report = generate_readable_report(ticker, report)
    
    # Visualize the analysis
    # fig = visualize_analysis(report)
    # plt.show()

if __name__ == "__main__":
    main()