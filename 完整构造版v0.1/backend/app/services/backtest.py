"""
Backtest engine service - portfolio backtesting with rolling weights support
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
from .weighting import WeightingService


@dataclass
class TransactionCost:
    """Transaction cost configuration"""
    buy_cost_pct: float = 0.001
    sell_cost_pct: float = 0.001
    buy_cost_fixed: float = 0.0
    sell_cost_fixed: float = 0.0
    slippage_pct: float = 0.0005


class BacktestService:
    """Backtest engine with rolling weights support"""
    
    def __init__(
        self, 
        returns_df: pd.DataFrame,
        baseline_asset: str
    ):
        self.returns_df = returns_df
        self.baseline_asset = baseline_asset
        
        if baseline_asset not in returns_df.columns:
            raise ValueError(f"Baseline asset {baseline_asset} not found")
        
        self.trade_log: List[Dict] = []
    
    def run_backtest(
        self,
        initial_value: float = 100000,
        rebalance_freq: str = 'monthly',
        transaction_costs: Optional[Dict[str, TransactionCost]] = None,
        use_rolling_weights: bool = False,
        weighting_method: str = 'equal_weight',
        warmup_period: int = 252,
        risk_free_rate: float = 0.03,
        allow_short: bool = False,
        static_weights: Optional[Dict[str, float]] = None,
        use_fixed_window: bool = False,
        rolling_window: int = 252
    ) -> Dict[str, Any]:
        """
        Run backtest (with rolling weights support)
        
        Args:
            initial_value: Initial portfolio value
            rebalance_freq: 'monthly', 'quarterly', 'yearly', 'none'
            transaction_costs: Per-asset transaction costs
            use_rolling_weights: Use rolling weight recalculation
            weighting_method: 'equal_weight', 'risk_parity', 'minimum_variance', 'maximum_sharpe'
            warmup_period: Days for initial weight calculation
            risk_free_rate: Annual risk-free rate
            allow_short: Allow short selling
            static_weights: Pre-calculated weights (if not rolling)
            use_fixed_window: Use fixed window vs cumulative
            rolling_window: Fixed window size in days
        """
        self.trade_log = []
        
        if static_weights is not None:
            assets = list(static_weights.keys())
        else:
            assets = [col for col in self.returns_df.columns if col != self.baseline_asset]
        
        if not assets:
            raise ValueError("No assets available")
        
        if transaction_costs is None:
            transaction_costs = {asset: TransactionCost() for asset in assets}
        
        asset_returns = self.returns_df[assets]
        
        if len(asset_returns) < warmup_period:
            raise ValueError(f"Data length {len(asset_returns)} < warmup period {warmup_period}")
        
        if not use_rolling_weights or weighting_method == 'equal_weight':
            if static_weights is None:
                warmup_returns = asset_returns.iloc[:warmup_period]
                engine = WeightingService(warmup_returns)
                weights = self._calculate_weights(engine, weighting_method, risk_free_rate, allow_short)
            else:
                weights = static_weights
            
            portfolio_returns, position_series = self._static_weights_backtest(
                asset_returns, weights, initial_value, rebalance_freq, transaction_costs
            )
        else:
            portfolio_returns, position_series = self._rolling_weights_backtest(
                asset_returns, weighting_method, warmup_period, initial_value,
                rebalance_freq, transaction_costs, risk_free_rate, allow_short,
                use_fixed_window, rolling_window
            )
        
        cumulative_returns = (1 + portfolio_returns).cumprod() - 1
        baseline_returns = self.returns_df[self.baseline_asset]
        baseline_cumulative = (1 + baseline_returns).cumprod() - 1
        
        metrics = self._calculate_metrics(portfolio_returns, baseline_returns)
        drawdown = self._calculate_drawdown(cumulative_returns)
        
        # 验算数据（保留原始 DataFrame 供 Excel 导出）
        validation_df = position_series.copy()
        validation_df['portfolio_nav'] = initial_value * (1 + cumulative_returns)
        validation_df['daily_return'] = portfolio_returns
        validation_df['cumulative_return'] = cumulative_returns
        
        rebalance_dates = [t['date'] for t in self.trade_log]
        validation_df['rebalance_flag'] = 0
        for date_str in rebalance_dates:
            if date_str in validation_df.index.astype(str):
                validation_df.loc[date_str, 'rebalance_flag'] = 1
        
        return {
            'metrics': metrics,
            'returns_series': self._series_to_dict(cumulative_returns, baseline_cumulative),
            'position_series': position_series,  # 保留原始 DataFrame
            'trade_log': self.trade_log,
            'validation_data': validation_df,    # 保留原始 DataFrame
            'daily_returns': {
                'portfolio': portfolio_returns.to_dict(),
                'baseline': baseline_returns.to_dict()
            }
        }
    
    def _calculate_weights(
        self, engine: WeightingService, method: str, 
        risk_free_rate: float, allow_short: bool
    ) -> Dict[str, float]:
        """Calculate weights based on method"""
        if method == 'equal_weight':
            return engine.equal_weight()
        elif method == 'risk_parity':
            return engine.risk_parity()
        elif method == 'minimum_variance':
            return engine.minimum_variance(allow_short)
        elif method == 'maximum_sharpe':
            return engine.maximum_sharpe(risk_free_rate, allow_short)
        else:
            return engine.equal_weight()
    
    def _static_weights_backtest(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        initial_value: float,
        rebalance_freq: str,
        transaction_costs: Dict[str, TransactionCost]
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """Static weights backtest"""
        
        rebalance_dates = self._get_rebalance_dates(returns, rebalance_freq)
        
        portfolio_returns = []
        current_weights = pd.Series(weights)
        current_value = initial_value
        positions = []  # 存储字典列表，后续转为 DataFrame
        
        for date, daily_ret in returns.iterrows():
            current_positions = current_weights * current_value
            positions.append(current_positions.to_dict())
            
            if date in rebalance_dates:
                target_weights = pd.Series(weights)
                target_positions = target_weights * current_value
                total_cost = 0.0
                
                for asset in weights.keys():
                    cost_config = transaction_costs.get(asset, TransactionCost())
                    position_change = target_positions[asset] - current_positions[asset]
                    
                    if abs(position_change) > 0:
                        if position_change > 0:
                            cost = abs(position_change) * cost_config.buy_cost_pct + cost_config.buy_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        else:
                            cost = abs(position_change) * cost_config.sell_cost_pct + cost_config.sell_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        
                        total_cost += cost + slippage
                
                self.trade_log.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'REBALANCE',
                    'total_cost': total_cost,
                    'portfolio_value': current_value
                })
                
                current_value -= total_cost
                current_weights = target_weights.copy()
            
            daily_return = (daily_ret * current_weights).sum()
            portfolio_returns.append(daily_return)
            current_value *= (1 + daily_return)
            
            current_weights = current_weights * (1 + daily_ret)
            current_weights = current_weights / current_weights.sum()
        
        return pd.Series(portfolio_returns, index=returns.index), pd.DataFrame(positions, index=returns.index)
    
    def _rolling_weights_backtest(
        self,
        returns: pd.DataFrame,
        weighting_method: str,
        warmup_period: int,
        initial_value: float,
        rebalance_freq: str,
        transaction_costs: Dict[str, TransactionCost],
        risk_free_rate: float,
        allow_short: bool,
        use_fixed_window: bool = False,
        rolling_window: int = 252
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """Rolling weights backtest"""
        
        rebalance_dates = self._get_rebalance_dates(returns, rebalance_freq)
        
        portfolio_returns = []
        current_value = initial_value
        positions = []
        
        warmup_returns = returns.iloc[:warmup_period]
        engine = WeightingService(warmup_returns)
        current_weights = pd.Series(self._calculate_weights(engine, weighting_method, risk_free_rate, allow_short))
        
        for i, (date, daily_ret) in enumerate(returns.iterrows()):
            if i < warmup_period:
                portfolio_returns.append(0.0)
                positions.append((current_weights * current_value).to_dict())
                continue
            
            current_positions = current_weights * current_value
            positions.append(current_positions.to_dict())
            
            if date in rebalance_dates:
                if use_fixed_window and i >= rolling_window:
                    historical_returns = returns.iloc[i-rolling_window+1:i+1]
                else:
                    historical_returns = returns.iloc[:i+1]
                
                engine = WeightingService(historical_returns)
                target_weights = pd.Series(self._calculate_weights(engine, weighting_method, risk_free_rate, allow_short))
                
                target_positions = target_weights * current_value
                total_cost = 0.0
                
                for asset in target_weights.index:
                    cost_config = transaction_costs.get(asset, TransactionCost())
                    position_change = target_positions[asset] - current_positions[asset]
                    
                    if abs(position_change) > 0:
                        if position_change > 0:
                            cost = abs(position_change) * cost_config.buy_cost_pct + cost_config.buy_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        else:
                            cost = abs(position_change) * cost_config.sell_cost_pct + cost_config.sell_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        
                        total_cost += cost + slippage
                
                self.trade_log.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'REBALANCE',
                    'weights': target_weights.to_dict(),
                    'total_cost': total_cost,
                    'portfolio_value': current_value
                })
                
                current_value -= total_cost
                current_weights = target_weights.copy()
            
            daily_return = (daily_ret * current_weights).sum()
            portfolio_returns.append(daily_return)
            current_value *= (1 + daily_return)
            
            current_weights = current_weights * (1 + daily_ret)
            current_weights = current_weights / current_weights.sum()
        
        return pd.Series(portfolio_returns, index=returns.index), pd.DataFrame(positions, index=returns.index)
    
    def _get_rebalance_dates(self, returns: pd.DataFrame, freq: str) -> list:
        """Get rebalance dates based on frequency"""
        if freq == 'monthly':
            return returns.resample('ME').first().index.tolist()
        elif freq == 'quarterly':
            return returns.resample('QE').first().index.tolist()
        elif freq == 'yearly':
            return returns.resample('YE').first().index.tolist()
        else:
            return []
    
    def _calculate_metrics(self, portfolio_returns: pd.Series, baseline_returns: pd.Series) -> Dict[str, float]:
        """Calculate performance metrics"""
        annual_return = portfolio_returns.mean() * 252
        annual_volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - 0.03) / annual_volatility if annual_volatility > 0 else 0
        
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        baseline_annual_return = baseline_returns.mean() * 252
        baseline_annual_vol = baseline_returns.std() * np.sqrt(252)
        excess_return = annual_return - baseline_annual_return
        
        tracking_error = (portfolio_returns - baseline_returns).std() * np.sqrt(252)
        information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
        
        win_days = (portfolio_returns > baseline_returns).sum()
        total_days = len(portfolio_returns)
        win_rate = win_days / total_days if total_days > 0 else 0
        
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        sortino_ratio = (annual_return - 0.03) / downside_std
        
        return {
            'annual_return': float(annual_return),
            'annual_volatility': float(annual_volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'calmar_ratio': float(calmar_ratio),
            'sortino_ratio': float(sortino_ratio),
            'baseline_return': float(baseline_annual_return),
            'baseline_volatility': float(baseline_annual_vol),
            'excess_return': float(excess_return),
            'information_ratio': float(information_ratio),
            'win_rate': float(win_rate),
            'total_trades': len(self.trade_log),
            'total_transaction_cost': float(sum(t['total_cost'] for t in self.trade_log))
        }
    
    def _calculate_drawdown(self, cumulative_returns: pd.Series) -> pd.Series:
        """Calculate drawdown series"""
        nav = 1 + cumulative_returns
        running_max = nav.cummax()
        drawdown = (nav - running_max) / running_max
        return drawdown
    
    def _series_to_dict(self, portfolio: pd.Series, baseline: pd.Series) -> Dict[str, Dict[str, float]]:
        """Convert returns series to dict format"""
        result = {}
        for date in portfolio.index:
            date_str = date.strftime('%Y-%m-%d')
            result[date_str] = {
                'portfolio': float(portfolio.loc[date]),
                'baseline': float(baseline.loc[date])
            }
        return result
    
    def _position_to_dict(self, position_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Convert position DataFrame to dict format"""
        result = {}
        for date in position_df.index:
            date_str = date.strftime('%Y-%m-%d')
            result[date_str] = {col: float(position_df.loc[date, col]) for col in position_df.columns}
        return result
