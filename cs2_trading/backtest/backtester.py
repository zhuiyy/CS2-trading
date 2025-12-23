import numpy as np
import pandas as pd
from typing import Dict, List, Any

class Backtester:
    def __init__(self, initial_capital: float = 10000.0, risk_free_rate: float = 0.0):
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate

    def run_backtest(self, price_series: Dict[str, List[float]], signals: Dict[str, List[int]]) -> Dict[str, Any]:
        """
        Run a simple vectorised backtest.
        
        Args:
            price_series: Dict mapping asset name to list of prices.
            signals: Dict mapping asset name to list of signals (1: buy, -1: sell, 0: hold).
                     Signals are assumed to be executed at the CLOSE of the same bar (simplified)
                     or OPEN of next bar depending on interpretation. 
                     For this scaffold, we'll assume signal at t acts on price change t to t+1.
        
        Returns:
            Dict containing performance metrics.
        """
        # Convert inputs to DataFrames for easier manipulation
        prices_df = pd.DataFrame(price_series)
        
        # If signals are empty or missing for some assets, fill with 0
        if not signals:
            signals_df = pd.DataFrame(0, index=prices_df.index, columns=prices_df.columns)
        else:
            signals_df = pd.DataFrame(signals)
            # Align signals with prices
            signals_df = signals_df.reindex(prices_df.index).fillna(0)

        # Calculate percentage returns of the assets: (P_t+1 - P_t) / P_t
        # We shift(-1) because return at time t is realized at t+1
        asset_returns = prices_df.pct_change().fillna(0)

        # Strategy returns: signal at t * return at t (realized at t)
        # Actually, usually signal calculated at t-1 is applied to return at t.
        # Let's assume signal[t] is the position held during period t (capturing return[t]).
        strategy_returns = signals_df * asset_returns

        # Portfolio return is the mean of active strategy returns (assuming equal weight for simplicity)
        # or sum if we treat signals as weights. Let's treat signals as weights.
        # If we have multiple assets, we sum the returns.
        portfolio_returns = strategy_returns.sum(axis=1)

        # Calculate metrics
        total_return = (1 + portfolio_returns).prod() - 1
        
        # Sharpe Ratio
        # Annualized assuming daily data (252 days)
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        if std_return == 0:
            sharpe = 0.0
        else:
            sharpe = (mean_return - self.risk_free_rate) / std_return * np.sqrt(252)

        return {
            "total_return": total_return,
            "sharpe": sharpe,
            "mean_return": mean_return,
            "std_return": std_return,
            "portfolio_returns": portfolio_returns.tolist()
        }
