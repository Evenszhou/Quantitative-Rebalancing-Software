# BL模型API设计更新（基于PyPortfolioOpt研究）

**日期**: 2026-04-27
**任务**: 1.1.2 研究开源实现

---

## ✅ 确认的API设计

### 核心类
```python
class BlackLittermanEngine:
    def __init__(
        self,
        returns_df: pd.DataFrame,
        market_caps: Dict[str, float],
        tau: float = 0.05,
        risk_free_rate: float = 0.03
    ):
        """自动计算均衡收益"""

    def add_absolute_view(
        self,
        asset: str,
        view_return: float,
        confidence: float = 0.5
    ) -> None:
        """添加绝对观点"""

    def add_relative_view(
        self,
        assets: List[str],
        view_returns: List[float],
        confidence: float = 0.5
    ) -> None:
        """添加相对观点"""

    def compute_weights(
        self,
        allow_short: bool = False,
        weight_bounds: Tuple[float, float] = (0, 1)
    ) -> pd.Series:
        """计算BL权重（一站式）"""

    def compare_with_benchmarks(
        self,
        weights: pd.Series
    ) -> pd.DataFrame:
        """对比不同配权方法"""
```

---

## 🛡️ 数值稳定性措施

### 1. 矩阵求逆
```python
def _safe_inverse(self, matrix: np.ndarray) -> np.ndarray:
    """安全的矩阵求逆"""
    try:
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(matrix)
```

### 2. 协方差矩阵正则化
```python
from sklearn.covariance import LedoitWolf

# 使用收缩估计
cov_regressor = LedoitWolf()
cov_matrix_reg = cov_regressor.fit(returns_df).covariance_
```

### 3. 条件数检查
```python
def _check_matrix_condition(self, matrix: np.ndarray, threshold: float = 1e10):
    """检查矩阵条件数"""
    cond = np.linalg.cond(matrix)
    if cond > threshold:
        warnings.warn(f"矩阵条件数{cond:.2e}过大，可能数值不稳定")
```

---

## 📝 参数验证清单

### 初始化验证
- [ ] returns_df不能为空
- [ ] market_caps与returns_df的资产匹配
- [ ] tau在合理范围内(0.001-0.1)
- [ ] risk_free_rate在合理范围内(0-0.1)

### 观点验证
- [ ] 资产存在于returns_df中
- [ ] confidence在[0,1]范围内
- [ ] view_return不能过大(警告)
- [ ] 相对观点的资产数量=2

### 优化验证
- [ ] 权重和为1（容差1e-6）
- [ ] 权重在边界内
- [ ] 优化成功（检查result.success）

---

## 🔧 实现细节（基于PyPortfolioOpt）

### 1. 均衡收益计算
```python
def _calculate_equilibrium_returns(self) -> pd.Series:
    """
    计算市场均衡收益

    Π = λ Σ w_market

    其中 λ = (E[R_m] - R_f) / σ_m²
    """
    # 计算市值权重
    total_cap = sum(self.market_caps.values())
    w_market = np.array([
        self.market_caps[asset] / total_cap
        for asset in self.assets
    ])

    # 计算市场组合指标
    market_return = np.dot(w_market, self.expected_returns)
    market_var = np.dot(w_market.T, np.dot(self.cov_matrix, w_market))

    # 风险厌恶系数
    risk_aversion = (market_return - self.risk_free_rate) / market_var

    # 均衡收益
    pi = risk_aversion * np.dot(self.cov_matrix, w_market)

    return pd.Series(pi, index=self.assets)
```

### 2. Ω计算（简化版）
```python
def _calculate_view_uncertainty(self, P: np.ndarray) -> np.ndarray:
    """
    计算观点不确定性矩阵Ω

    使用简化公式: Ω_ii = (1/conf - 1) × P_i Σ P_i'
    """
    n_views = len(self.views)
    Omega = np.zeros((n_views, n_views))

    for i, view in enumerate(self.views):
        conf = view['confidence']
        p_i = P[i, :].reshape(1, -1)

        # 观点方差
        var = np.dot(p_i, np.dot(self.cov_matrix, p_i.T))[0, 0]

        # 调整
        Omega[i, i] = var * (1 / conf - 1)

    return Omega
```

### 3. 后验收益计算
```python
def _calculate_posterior_returns(
    self,
    equilibrium_returns: pd.Series,
    P: np.ndarray,
    Q: np.ndarray,
    Omega: np.ndarray
) -> pd.Series:
    """
    计算后验期望收益

    E[R] = M1^(-1) × M2

    其中:
    M1 = (τΣ)^(-1) + P'Ω^(-1)P
    M2 = (τΣ)^(-1)Π + P'Ω^(-1)Q
    """
    # τΣ
    tau_sigma = self.tau * self.cov_matrix
    tau_sigma_inv = self._safe_inverse(tau_sigma)

    # 如果没有观点，返回均衡收益
    if P is None:
        return equilibrium_returns

    # Ω^(-1)
    Omega_inv = self._safe_inverse(Omega)

    # M1 = (τΣ)^(-1) + P'Ω^(-1)P
    M1 = tau_sigma_inv + np.dot(P.T, np.dot(Omega_inv, P))

    # M2 = (τΣ)^(-1)Π + P'Ω^(-1)Q
    M2 = np.dot(tau_sigma_inv, equilibrium_returns)
    M2 += np.dot(P.T, np.dot(Omega_inv, Q))

    # 求解
    M1_inv = self._safe_inverse(M1)
    posterior = np.dot(M1_inv, M2)

    return pd.Series(posterior, index=self.assets)
```

---

## 🎯 对比功能设计

```python
def compare_with_benchmarks(
    self,
    weights: pd.Series
) -> pd.DataFrame:
    """
    对比不同配权方法

    Returns:
        DataFrame with columns:
        - BL权重
        - 市值权重
        - 等权
        - 最小方差权重
        - 风险平价权重
    """
    from utils.weighting import WeightingEngine

    # 计算各种权重
    engine = WeightingEngine(self.returns_df)

    comparisons = {
        'BL权重': weights,
        '市值权重': pd.Series(self.market_weights),
        '等权': engine.equal_weight(),
        '最小方差': engine.minimum_variance(),
        '风险平价': engine.risk_parity(),
    }

    return pd.DataFrame(comparisons)
```

---

## 📊 单元测试计划

### 测试用例
1. **test_no_views**: 无观点时，应该接近市值权重
2. **test_absolute_view**: 绝对观点后，该资产收益调整
3. **test_relative_view**: 相对观点后，两个资产差异调整
4. **test_high_confidence**: 高置信度时，权重倾向于观点
5. **test_low_confidence**: 低置信度时，权重倾向于市场
6. **test_multiple_views**: 多个观点的综合效果
7. **test_extreme_confidence**: 置信度=1时，完全相信观点
8. **test_zero_confidence**: 置信度→0时，观点无影响

---

## ✅ 下一步

**任务1.1.3**: 设计我们的API
- 基于PyPortfolioOpt的分析
- 确定最终API设计
- 编写接口文档

**任务1.2**: 开始编码实现
- 创建utils/bl_portfolio.py
- 实现核心算法
- 编写测试
