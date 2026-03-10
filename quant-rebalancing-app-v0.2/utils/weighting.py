"""
配权算法模块
实现多种资产配置策略
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Optional


class WeightingEngine:
    """配权引擎"""
    
    def __init__(self, returns_df: pd.DataFrame):
        """
        初始化配权引擎
        
        Args:
            returns_df: 收益率数据框，列为资产名，索引为日期
        """
        self.returns_df = returns_df
        self.assets = returns_df.columns.tolist()
        self.n_assets = len(self.assets)
        
        # 计算协方差矩阵（年化）
        self.cov_matrix = returns_df.cov() * 252
        
        # 计算期望收益率（年化）
        self.expected_returns = returns_df.mean() * 252
        
        # 计算波动率（年化）
        self.volatilities = returns_df.std() * np.sqrt(252)
    
    def equal_weight(self) -> pd.Series:
        """
        等权配权
        
        Returns:
            pd.Series: 权重序列
        """
        weights = pd.Series(1.0 / self.n_assets, index=self.assets)
        return weights
    
    def risk_parity(self, target_risk: Optional[np.ndarray] = None) -> pd.Series:
        """
        风险平价配权
        每个资产对组合总风险的贡献相等
        
        Args:
            target_risk: 目标风险预算，默认为等风险贡献
            
        Returns:
            pd.Series: 权重序列
        """
        # 默认等风险贡献
        if target_risk is None:
            target_risk = np.ones(self.n_assets) / self.n_assets
        
        # 初始猜测
        w0 = np.ones(self.n_assets) / self.n_assets
        
        # 目标函数：最小化风险贡献的方差
        def objective(w):
            # 组合波动率
            port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
            
            # 边际风险贡献
            mrc = np.dot(self.cov_matrix, w) / port_vol
            
            # 风险贡献
            rc = w * mrc
            
            # 归一化
            rc = rc / rc.sum()
            
            # 目标：风险贡献与目标风险预算的差异
            return np.sum((rc - target_risk) ** 2)
        
        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # 权重和为1
        ]
        
        # 边界条件（权重非负）
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        # 优化
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"风险平价优化失败: {result.message}")
        
        weights = pd.Series(result.x, index=self.assets)
        
        # 归一化（确保和为1）
        weights = weights / weights.sum()
        
        return weights
    
    def minimum_variance(self, allow_short: bool = False) -> pd.Series:
        """
        最小方差配权
        最小化组合方差
        
        Args:
            allow_short: 是否允许做空
            
        Returns:
            pd.Series: 权重序列
        """
        # 初始猜测
        w0 = np.ones(self.n_assets) / self.n_assets
        
        # 目标函数：组合方差
        def objective(w):
            return np.dot(w.T, np.dot(self.cov_matrix, w))
        
        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # 权重和为1
        ]
        
        # 边界条件
        if allow_short:
            bounds = None  # 无限制
        else:
            bounds = tuple((0, 1) for _ in range(self.n_assets))  # 非负
        
        # 优化
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"最小方差优化失败: {result.message}")
        
        weights = pd.Series(result.x, index=self.assets)
        
        return weights
    
    def maximum_sharpe(
        self, 
        risk_free_rate: float = 0.03,
        allow_short: bool = False
    ) -> pd.Series:
        """
        最大夏普比率配权
        最大化风险调整后收益
        
        Args:
            risk_free_rate: 无风险利率（年化）
            allow_short: 是否允许做空
            
        Returns:
            pd.Series: 权重序列
        """
        # 初始猜测
        w0 = np.ones(self.n_assets) / self.n_assets
        
        # 目标函数：负夏普比率（因为要用minimize）
        def neg_sharpe(w):
            # 组合收益率
            port_return = np.dot(w, self.expected_returns)
            
            # 组合波动率
            port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
            
            # 夏普比率
            sharpe = (port_return - risk_free_rate) / port_vol
            
            return -sharpe  # 返回负值用于最小化
        
        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]
        
        # 边界条件
        if allow_short:
            bounds = None
        else:
            bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        # 优化
        result = minimize(
            neg_sharpe,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            raise ValueError(f"最大夏普优化失败: {result.message}")
        
        weights = pd.Series(result.x, index=self.assets)
        
        return weights
    
    def get_portfolio_metrics(self, weights: pd.Series) -> Dict[str, float]:
        """
        计算组合绩效指标
        
        Args:
            weights: 权重序列
            
        Returns:
            dict: 绩效指标
        """
        w = weights.values
        
        # 年化收益率
        port_return = np.dot(w, self.expected_returns)
        
        # 年化波动率
        port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
        
        # 夏普比率（假设无风险利率3%）
        sharpe = (port_return - 0.03) / port_vol
        
        # 风险贡献
        mrc = np.dot(self.cov_matrix, w) / port_vol
        rc = w * mrc
        rc_pct = rc / rc.sum()
        
        return {
            'annual_return': port_return,
            'annual_volatility': port_vol,
            'sharpe_ratio': sharpe,
            'risk_contributions': dict(zip(self.assets, rc_pct))
        }
    
    def validate_weights(self, weights: pd.Series) -> bool:
        """
        验证权重是否有效
        
        Args:
            weights: 权重序列
            
        Returns:
            bool: 是否有效
        """
        # 检查权重和是否为1
        if abs(weights.sum() - 1.0) > 1e-6:
            return False
        
        # 检查是否有负权重
        if (weights < 0).any():
            return False
        
        return True
