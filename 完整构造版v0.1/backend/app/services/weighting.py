"""
Weighting engine service - portfolio optimization algorithms
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Optional


class WeightingService:
    """Service for portfolio weight optimization"""
    
    def __init__(self, returns_df: pd.DataFrame):
        """
        Initialize weighting service
        
        Args:
            returns_df: DataFrame with asset returns (columns=assets, index=dates)
        """
        self.returns_df = returns_df
        self.assets = returns_df.columns.tolist()
        self.n_assets = len(self.assets)
        
        self.cov_matrix = returns_df.cov() * 252
        self.expected_returns = returns_df.mean() * 252
        self.volatilities = returns_df.std() * np.sqrt(252)
    
    def equal_weight(self) -> Dict[str, float]:
        """Equal weight allocation"""
        weights = {asset: 1.0 / self.n_assets for asset in self.assets}
        return weights
    
    def risk_parity(self, target_risk: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Risk parity allocation - equal risk contribution
        
        Args:
            target_risk: Target risk budget (default: equal)
            
        Returns:
            Dict of asset weights
        """
        if target_risk is None:
            target_risk = np.ones(self.n_assets) / self.n_assets
        
        w0 = np.ones(self.n_assets) / self.n_assets
        
        def objective(w):
            port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix.values, w)))
            mrc = np.dot(self.cov_matrix.values, w) / port_vol
            rc = w * mrc
            rc = rc / rc.sum()
            return np.sum((rc - target_risk) ** 2)
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        result = minimize(
            objective, w0, method='SLSQP', bounds=bounds,
            constraints=constraints, options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"Risk parity optimization failed: {result.message}")
        
        weights = result.x
        weights = weights / weights.sum()
        
        return {asset: float(w) for asset, w in zip(self.assets, weights)}
    
    def minimum_variance(self, allow_short: bool = False) -> Dict[str, float]:
        """
        Minimum variance allocation
        
        Args:
            allow_short: Allow negative weights
            
        Returns:
            Dict of asset weights
        """
        w0 = np.ones(self.n_assets) / self.n_assets
        
        def objective(w):
            return np.dot(w.T, np.dot(self.cov_matrix.values, w))
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        bounds = None if allow_short else tuple((0, 1) for _ in range(self.n_assets))
        
        result = minimize(
            objective, w0, method='SLSQP', bounds=bounds,
            constraints=constraints, options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"Minimum variance optimization failed: {result.message}")
        
        return {asset: float(w) for asset, w in zip(self.assets, result.x)}
    
    def maximum_sharpe(
        self, 
        risk_free_rate: float = 0.03,
        allow_short: bool = False
    ) -> Dict[str, float]:
        """
        Maximum Sharpe ratio allocation
        
        Args:
            risk_free_rate: Annual risk-free rate
            allow_short: Allow negative weights
            
        Returns:
            Dict of asset weights
        """
        w0 = np.ones(self.n_assets) / self.n_assets
        
        def neg_sharpe(w):
            port_return = np.dot(w, self.expected_returns.values)
            port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix.values, w)))
            sharpe = (port_return - risk_free_rate) / port_vol
            return -sharpe
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        bounds = None if allow_short else tuple((0, 1) for _ in range(self.n_assets))
        
        result = minimize(
            neg_sharpe, w0, method='SLSQP', bounds=bounds,
            constraints=constraints, options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"Maximum Sharpe optimization failed: {result.message}")
        
        return {asset: float(w) for asset, w in zip(self.assets, result.x)}
    
    def get_portfolio_metrics(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate portfolio metrics
        
        Args:
            weights: Dict of asset weights
            
        Returns:
            Dict of portfolio metrics
        """
        w = np.array([weights.get(asset, 0) for asset in self.assets])
        
        port_return = np.dot(w, self.expected_returns.values)
        port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix.values, w)))
        sharpe = (port_return - 0.03) / port_vol if port_vol > 0 else 0
        
        mrc = np.dot(self.cov_matrix.values, w) / port_vol if port_vol > 0 else np.zeros(self.n_assets)
        rc = w * mrc
        rc_pct = rc / rc.sum() if rc.sum() > 0 else np.zeros(self.n_assets)
        
        return {
            'annual_return': float(port_return),
            'annual_volatility': float(port_vol),
            'sharpe_ratio': float(sharpe),
            'risk_contributions': {asset: float(p) for asset, p in zip(self.assets, rc_pct)}
        }
    
    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """Validate weights sum to 1 and non-negative"""
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-6:
            return False
        if any(w < 0 for w in weights.values()):
            return False
        return True
