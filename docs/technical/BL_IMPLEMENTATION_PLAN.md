# Black-Litterman模型技术实现方案

**版本**: v1.0
**创建日期**: 2026-04-27
**预计完成**: 2026-05-10

---

## 📋 需求概述

### 功能需求
1. 支持研究员输入投研观点（看好/看空某资产）
2. 基于观点和市场均衡，计算后验收益
3. 优化投资组合权重
4. 对比分析：BL权重 vs 等权 vs 市场权重

### 非功能需求
1. **可解释性**: IC能理解为什么给出这个权重
2. **稳定性**: 参数变化时权重不应该剧烈波动
3. **性能**: 计算时间 < 1秒（对于20个资产）
4. **可测试性**: 单元测试覆盖率 > 80%

---

## 🎯 API设计

### 核心类：BlackLittermanEngine

```python
class BlackLittermanEngine:
    """Black-Litterman配权引擎"""

    def __init__(
        self,
        returns_df: pd.DataFrame,
        market_caps: Dict[str, float],
        tau: float = 0.05,
        risk_free_rate: float = 0.03
    ):
        """
        初始化BL引擎

        Args:
            returns_df: 收益率数据，索引为日期，列为资产
            market_caps: 市值字典 {资产: 市值}
            tau: 不确定性参数，默认0.05
            risk_free_rate: 无风险利率，默认3%
        """
        pass

    def add_absolute_view(
        self,
        asset: str,
        view_return: float,
        confidence: float = 0.5
    ) -> None:
        """
        添加绝对观点

        Args:
            asset: 资产名称
            view_return: 预期超额收益（如0.05表示5%）
            confidence: 置信度 [0, 1]，0.5表示中等信心
        """
        pass

    def add_relative_view(
        self,
        assets: List[str],
        view_returns: List[float],
        confidence: float = 0.5
    ) -> None:
        """
        添加相对观点

        Args:
            assets: 涉及的资产列表
            view_returns: 相对收益（如[0.03, -0.03]表示A比B高3%）
            confidence: 置信度 [0, 1]
        """
        pass

    def compute_weights(
        self,
        allow_short: bool = False,
        weight_bounds: Tuple[float, float] = (0, 1)
    ) -> pd.Series:
        """
        计算BL权重

        Args:
            allow_short: 是否允许做空
            weight_bounds: 权重边界

        Returns:
            pd.Series: 资产权重
        """
        pass

    def get_portfolio_metrics(
        self,
        weights: pd.Series
    ) -> Dict[str, float]:
        """
        计算组合指标

        Args:
            weights: 权重序列

        Returns:
            dict: 包含年化收益、波动率、夏普比率等
        """
        pass

    def compare_with_benchmarks(
        self,
        weights: pd.Series
    ) -> pd.DataFrame:
        """
        对比不同配权方法

        Args:
            weights: BL权重

        Returns:
            pd.DataFrame: 对比表格
        """
        pass
```

---

## 🔬 核心算法实现

### 1. 计算市场均衡收益

```python
def _calculate_equilibrium_returns(self) -> pd.Series:
    """
    计算市场均衡收益（隐含收益）

    公式: Π = λ Σ w_market

    其中:
    - λ = (E[R_m] - R_f) / σ_m²  (风险厌恶系数)
    - Σ: 协方差矩阵
    - w_market: 市值权重

    Returns:
        pd.Series: 均衡收益
    """
    # 计算市值权重
    total_market_cap = sum(self.market_caps.values())
    market_weights = pd.Series({
        asset: cap / total_market_cap
        for asset, cap in self.market_caps.items()
    })

    # 计算市场组合收益和波动
    market_return = np.dot(market_weights, self.expected_returns)
    market_var = np.dot(market_weights.T, np.dot(self.cov_matrix, market_weights))
    market_vol = np.sqrt(market_var)

    # 计算风险厌恶系数
    # lambda = (E[R_m] - R_f) / σ_m²
    risk_aversion = (market_return - self.risk_free_rate) / market_var

    # 计算均衡收益
    # Π = λ Σ w_market
    equilibrium_returns = risk_aversion * np.dot(self.cov_matrix, market_weights)

    return pd.Series(equilibrium_returns, index=self.assets)
```

### 2. 构造观点矩阵

```python
def _build_view_matrices(self) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    构造观点矩阵P和观点收益向量Q

    Returns:
        P: 观点矩阵 (k x n), k=观点数, n=资产数
        Q: 观点收益向量 (k x 1)
    """
    if not self.views:
        return None, None

    n_assets = len(self.assets)
    n_views = len(self.views)

    P = np.zeros((n_views, n_assets))
    Q = np.zeros(n_views)

    for i, view in enumerate(self.views):
        if view['type'] == 'absolute':
            # 绝对观点: P = [0, ..., 1, ..., 0]
            asset_idx = self.assets.index(view['asset'])
            P[i, asset_idx] = 1.0
            Q[i] = view['return']

        elif view['type'] == 'relative':
            # 相对观点: P = [0, ..., 1, ..., -1, ..., 0]
            for asset, coeff in zip(view['assets'], view['returns']):
                asset_idx = self.assets.index(asset)
                P[i, asset_idx] = coeff
            Q[i] = 0  # 相对观点的Q通常为0

    return P, Q
```

### 3. 计算观点不确定性矩阵

```python
def _calculate_view_uncertainty(self, P: np.ndarray) -> np.ndarray:
    """
    计算观点不确定性矩阵Ω

    方法1: 基于置信度的对角矩阵
    Ω_ii = (1/confidence - 1) * P Σ P'

    方法2: Idzorek方法
    根据置信度反推Ω

    Args:
        P: 观点矩阵

    Returns:
        Ω: 观点不确定性矩阵 (k x k)
    """
    n_views = P.shape[0]
    Omega = np.zeros((n_views, n_views))

    for i, view in enumerate(self.views):
        confidence = view['confidence']

        # 计算该观点的方差
        # var = P_i Σ P_i'
        p_i = P[i, :].reshape(1, -1)
        var_i = np.dot(p_i, np.dot(self.cov_matrix, p_i.T))[0, 0]

        # 基于置信度调整
        # confidence高 -> Omega小
        # confidence低 -> Omega大
        Omega[i, i] = var_i * (1 / confidence - 1)

    return Omega
```

### 4. 计算后验收益

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

    公式:
    E[R] = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) [(τΣ)^(-1)Π + P'Ω^(-1)Q]

    Args:
        equilibrium_returns: 均衡收益 Π
        P: 观点矩阵
        Q: 观点收益向量
        Omega: 观点不确定性矩阵

    Returns:
        pd.Series: 后验收益
    """
    # 计算中间矩阵
    tau_sigma = self.tau * self.cov_matrix
    tau_sigma_inv = np.linalg.inv(tau_sigma)

    # 如果没有观点，返回均衡收益
    if P is None:
        return equilibrium_returns

    # 计算 (τΣ)^(-1) + P'Ω^(-1)P
    Omega_inv = np.linalg.inv(Omega)
    M1 = tau_sigma_inv + np.dot(P.T, np.dot(Omega_inv, P))

    # 计算 (τΣ)^(-1)Π + P'Ω^(-1)Q
    M2 = np.dot(tau_sigma_inv, equilibrium_returns) + np.dot(P.T, np.dot(Omega_inv, Q))

    # 求解
    M1_inv = np.linalg.inv(M1)
    posterior_returns = np.dot(M1_inv, M2)

    return pd.Series(posterior_returns, index=self.assets)
```

### 5. 优化权重

```python
def _optimize_weights(
    self,
    expected_returns: pd.Series,
    allow_short: bool = False,
    weight_bounds: Tuple[float, float] = (0, 1)
) -> pd.Series:
    """
    基于后验收益优化权重

    使用均值-方差优化，最大化夏普比率

    Args:
        expected_returns: 期望收益
        allow_short: 是否允许做空
        weight_bounds: 权重边界

    Returns:
        pd.Series: 最优权重
    """
    n_assets = len(self.assets)

    # 目标函数：负夏普比率
    def neg_sharpe(weights):
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_var = np.dot(weights.T, np.dot(self.cov_matrix, weights))
        portfolio_vol = np.sqrt(portfolio_var)
        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
        return -sharpe

    # 约束条件
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # 权重和为1
    ]

    # 边界条件
    if allow_short:
        bounds = None  # 无限制
    else:
        bounds = tuple(weight_bounds for _ in range(n_assets))

    # 初始猜测
    w0 = np.ones(n_assets) / n_assets

    # 优化
    result = minimize(
        neg_sharpe,
        w0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000, 'ftol': 1e-9}
    )

    if not result.success:
        raise ValueError(f"优化失败: {result.message}")

    weights = pd.Series(result.x, index=self.assets)
    return weights
```

---

## 🧪 测试方案

### 单元测试

```python
# tests/test_bl_portfolio.py

def test_equilibrium_returns():
    """测试均衡收益计算"""
    # 使用已知数据验证
    pass

def test_absolute_view():
    """测试绝对观点"""
    # 添加观点后，该资产的收益应该调整
    pass

def test_relative_view():
    """测试相对观点"""
    # 添加相对观点后，两个资产的收益差异应该调整
    pass

def test_no_views():
    """测试无观点情况"""
    # 无观点时，应该接近市值权重
    pass

def test_high_confidence():
    """测试高置信度观点"""
    # 置信度高时，权重应该更倾向于观点
    pass

def test_low_confidence():
    """测试低置信度观点"""
    # 置信度低时，权重应该更接近市场权重
    pass

def test_multiple_views():
    """测试多个观点"""
    pass

def test_optimization():
    """测试优化过程"""
    pass
```

### 集成测试

```python
def test_full_pipeline():
    """测试完整流程"""
    # 1. 创建引擎
    # 2. 添加观点
    # 3. 计算权重
    # 4. 验证结果合理性
    pass

def test_comparison_with_benchmarks():
    """测试对比功能"""
    pass
```

---

## 📊 Streamlit界面设计

### 页面6: 投研观点管理

```python
# app.py

elif page == "6. 投研观点管理 (Black-Litterman)":
    st.header("💡 投研观点管理")

    # === 左侧：观点录入 ===
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("添加观点")

        # 选择观点类型
        view_type = st.radio(
            "观点类型",
            ["绝对观点", "相对观点"],
            help="绝对观点：某资产的预期收益\n相对观点：两个资产的相对表现"
        )

        # 输入观点
        if view_type == "绝对观点":
            asset = st.selectbox("资产", options=assets)
            view_return = st.number_input(
                "预期超额收益（%）",
                min_value=-20.0,
                max_value=20.0,
                value=5.0,
                step=0.5
            ) / 100
            confidence = st.slider(
                "置信度",
                min_value=0,
                max_value=100,
                value=70
            ) / 100

            if st.button("添加观点", type="primary"):
                bl_engine.add_absolute_view(asset, view_return, confidence)
                st.success(f"✅ 已添加观点: {asset} 预期收益 {view_return:.2%}")

        else:  # 相对观点
            assets_pair = st.multiselect("选择两个资产", options=assets, max_selections=2)
            if len(assets_pair) == 2:
                spread = st.number_input(
                    "相对差异（%）",
                    min_value=-20.0,
                    max_value=20.0,
                    value=3.0,
                    step=0.5
                ) / 100
                confidence = st.slider("置信度", 0, 100, 60) / 100

                if st.button("添加观点", type="primary"):
                    bl_engine.add_relative_view(
                        assets_pair,
                        [spread, -spread],
                        confidence
                    )
                    st.success(f"✅ 已添加相对观点")

    # === 右侧：观点列表和结果 ===
    with col2:
        st.subheader("当前观点")

        # 观点列表
        if bl_engine.views:
            for i, view in enumerate(bl_engine.views):
                with st.expander(f"观点 {i+1}", expanded=True):
                    if view['type'] == 'absolute':
                        st.write(f"**资产**: {view['asset']}")
                        st.write(f"**预期收益**: {view['return']:.2%}")
                    else:
                        st.write(f"**资产**: {view['assets']}")
                        st.write(f"**相对收益**: {view['returns']}")
                    st.write(f"**置信度**: {view['confidence']:.0%}")

        # 计算按钮
        if st.button("计算BL权重", type="primary"):
            with st.spinner("计算中..."):
                weights = bl_engine.compute_weights()

                # 显示结果
                st.subheader("配权结果")

                # 权重表格
                weights_df = pd.DataFrame({
                    '资产': weights.index,
                    'BL权重': weights.values,
                    '市值权重': [bl_engine.market_weights.get(a, 0) for a in weights.index],
                    '等权': 1.0 / len(weights)
                })
                st.dataframe(weights_df, use_container_width=True)

                # 对比图表
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='BL权重',
                    x=weights_df['资产'],
                    y=weights_df['BL权重']
                ))
                fig.add_trace(go.Bar(
                    name='市值权重',
                    x=weights_df['资产'],
                    y=weights_df['市值权重']
                ))
                fig.update_layout(barmode='group', title="权重对比")
                st.plotly_chart(fig, use_container_width=True)
```

---

## 📝 实现检查清单

### Week 1: 理论和算法
- [ ] 阅读BL模型理论文档
- [ ] 理解核心公式和参数
- [ ] 设计API接口
- [ ] 实现均衡收益计算
- [ ] 实现观点矩阵构造
- [ ] 实现观点不确定性计算
- [ ] 实现后验收益计算
- [ ] 实现权重优化

### Week 2: 测试和集成
- [ ] 编写单元测试
- [ ] 测试边界情况
- [ ] 回测验证
- [ ] Streamlit界面开发
- [ ] 集成测试
- [ ] 文档编写

---

## 🔍 关键参数调优

### tau (τ) 参数
- **默认值**: 0.05
- **范围**: 0.01 - 0.1
- **影响**: τ越小，观点影响越大
- **调优**: 通过参数敏感性分析确定

### confidence (置信度)
- **范围**: 0 - 1
- **影响**:
  - confidence = 1: 完全相信观点
  - confidence = 0.5: 观点和市场各占一半
  - confidence = 0: 不相信观点

### 建议的参数组合
```python
# 保守型
tau = 0.05
confidence = 0.5

# 激进型
tau = 0.03
confidence = 0.8

# 稳健型
tau = 0.1
confidence = 0.3
```

---

## 📚 参考资料

### 必读文献
1. Idzorek, R. (2007). "A Step-by-Step Guide to the Black-Litterman Model"
2. Black, F. & Litterman, R. (1992). "Global Portfolio Optimization"
3. Walters, J. (2014). "The Black-Litterman Model in Detail"

### 代码参考
- PyPortfolioOpt: https://pyportfolioopt.readthedocs.io/
- 公开实现示例

---

## 🎯 验收标准

- [ ] 核心算法实现完成
- [ ] 单元测试通过，覆盖率 > 80%
- [ ] Streamlit界面可用
- [ ] 能添加/删除观点
- [ ] 能计算BL权重
- [ ] 能对比不同配权方法
- [ ] 回测验证合理
- [ ] 代码有注释和文档

---

## 🚧 风险和注意事项

### 数值稳定性
- 协方差矩阵可能病态
- 使用正则化或收缩估计
- 检查矩阵条件数

### 边界情况
- 所有资产都有观点
- 观点冲突（互相矛盾）
- 极端置信度（0或1）

### 性能
- 大规模资产（>100）的优化速度
- 考虑使用更快的优化器

---

**备注**: 本文档是技术实现方案，编码时严格按照此方案执行。
