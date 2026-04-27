"""
Black-Litterman模型实现
========================

这是一个为投资组合配权设计的Black-Litterman模型实现。

BL模型的核心思想：
1. 从市场市值权重出发，计算隐含的均衡收益
2. 融合投研团队的观点（看涨/看跌某个资产）
3. 通过贝叶斯方法，综合市场和观点，得到后验收益
4. 基于后验收益优化投资组合权重

主要特点：
- 易用的API：添加观点很简单
- 灵活的置信度设置
- 自动数值稳定性处理
- 详细的注释，适合Python新手

使用示例：
    >>> from utils.bl_portfolio import BlackLittermanEngine
    >>> from utils.tushare_loader import TushareLoader
    >>>
    >>> # 获取数据
    >>> loader = TushareLoader()
    >>> returns_df = loader.get_returns(['000001.SZ', '600000.SH'], '2020-01-01')
    >>> market_caps = loader.get_market_caps(['000001.SZ', '600000.SH'])
    >>>
    >>> # 创建BL引擎
    >>> bl = BlackLittermanEngine(returns_df, market_caps, tau=0.05)
    >>>
    >>> # 添加观点
    >>> bl.add_absolute_view('000001.SZ', 0.10, confidence=0.7)
    >>>
    >>> # 计算权重
    >>> weights = bl.compute_weights()
    >>> print(weights)

作者：AI助手
创建日期：2026-04-27
版本：v1.0
"""

import pandas as pd  # pandas：数据处理库，类似于Excel
import numpy as np  # numpy：数值计算库，用于矩阵运算
from scipy.optimize import minimize  # scipy：科学计算库，minimize用于优化求解
from typing import Dict, List, Tuple, Optional, Union  # typing：类型提示，让代码更清晰
import warnings  # warnings：警告模块


class BlackLittermanEngine:
    """
    Black-Litterman配权引擎

    这个类实现了完整的Black-Litterman模型流程：
    1. 计算市场均衡收益（市场隐含的收益预期）
    2. 接收投研观点（看涨/看跌）
    3. 综合市场和观点，计算后验收益
    4. 优化投资组合权重

    参数说明：
        returns_df (pd.DataFrame): 收益率数据
            - 行：日期（时间序列）
            - 列：资产名称（如股票代码）
            - 值：收益率（小数形式，如0.05表示5%）

        market_caps (Dict[str, float]): 市值字典
            - 键：资产名称（如'000001.SZ'）
            - 值：市值（单位：元）
            - 例如：{'000001.SZ': 300000000000} 表示3000亿元

        tau (float): 不确定性参数，默认0.05
            - 这是一个很小的正数，通常在0.01到0.1之间
            - tau越小，观点的影响越大
            - tau越大，市场均衡的影响越大
            - 推荐值：0.05（经验值）

        risk_free_rate (float): 无风险利率，默认0.03（3%）
            - 这是完全无风险投资的年化收益率
            - 通常用国债利率代替
            - 用于计算夏普比率

    属性说明：
        views (List[Dict]): 观点列表
            - 每个观点是一个字典
            - 包含：类型、资产、收益、置信度

        market_weights (Dict[str, float]): 市值权重
            - 从market_caps计算得到
            - 表示每个资产在总市值中的占比

        cov_matrix (pd.DataFrame): 协方差矩阵
            - 描述资产之间的波动关系
            - 对角线：单个资产的方差
            - 非对角线：资产之间的协方差

        expected_returns (pd.Series): 期望收益
            - 历史平均收益的年化值
            - 用于计算市场均衡收益
    """

    def __init__(
        self,
        returns_df: pd.DataFrame,
        market_caps: Dict[str, float],
        tau: float = 0.05,
        risk_free_rate: float = 0.03
    ):
        """
        初始化BL引擎

        这个方法做了以下几件事：
        1. 保存输入的数据（收益率、市值、参数）
        2. 计算一些基础指标（协方差矩阵、期望收益、市值权重）
        3. 初始化观点列表（初始为空）

        参数：
            详见类文档

        返回：
            无（只是初始化对象）
        """
        # ========== 1. 保存输入数据 ==========

        # 保存收益率数据
        # returns_df是一个DataFrame，例如：
        #              000001.SZ  600000.SH
        # 2020-01-02   0.01      0.005
        # 2020-01-03  -0.005     0.002
        self.returns_df = returns_df

        # 获取资产列表（DataFrame的列名）
        # 例如：['000001.SZ', '600000.SH']
        self.assets = returns_df.columns.tolist()

        # 资产数量
        # 例如：2
        self.n_assets = len(self.assets)

        # 保存市值数据
        self.market_caps = market_caps

        # 保存BL模型参数
        self.tau = tau  # 不确定性参数
        self.risk_free_rate = risk_free_rate  # 无风险利率

        # ========== 2. 计算基础指标 ==========

        # 计算协方差矩阵（年化）
        # 步骤：
        # 1. returns_df.cov() 计算日收益率的协方差
        # 2. 乘以252（一年大约252个交易日）得到年化协方差
        #
        # 协方差矩阵示例：
        #              000001.SZ    600000.SH
        # 000001.SZ     0.04         0.01
        # 600000.SH     0.01         0.09
        # 解释：
        # - 对角线0.04和0.09是方差（波动率的平方）
        # - 非对角线0.01是协方差（两个资产一起变动的程度）
        self.cov_matrix = returns_df.cov() * 252

        # 计算期望收益（年化）
        # 步骤：
        # 1. returns_df.mean() 计算每个资产的日平均收益
        # 2. 乘以252得到年化收益
        #
        # 返回一个Series，例如：
        # 000001.SZ    0.08
        # 600000.SH    0.12
        self.expected_returns = returns_df.mean() * 252

        # 计算波动率（年化）
        # 步骤：
        # 1. returns_df.std() 计算每个资产的日标准差
        # 2. 乘以sqrt(252)得到年化波动率
        self.volatilities = returns_df.std() * np.sqrt(252)

        # ========== 3. 计算市值权重 ==========

        # 市值权重 = 每个资产的市值 / 总市值
        total_market_cap = sum(market_caps.values())

        # 用字典推导式计算
        # 例如：{'000001.SZ': 0.6, '600000.SH': 0.4}
        # 表示第一个资产占总市值的60%
        self.market_weights = {
            asset: cap / total_market_cap
            for asset, cap in market_caps.items()
        }

        # 转换为pandas Series，方便后续计算
        self.market_weights_series = pd.Series(self.market_weights)

        # ========== 4. 初始化观点列表 ==========

        # views是一个列表，存储所有添加的观点
        # 每个观点是一个字典，包含：
        # {
        #     'type': 'absolute' 或 'relative',
        #     'asset': '资产名称'（绝对观点）,
        #     'assets': ['资产1', '资产2']（相对观点）,
        #     'return': 预期收益,
        #     'returns': [收益1, 收益2]（相对观点）,
        #     'confidence': 置信度
        # }
        self.views = []

        # 计算市场均衡收益（后面会用到）
        # 这是BL模型的关键：从市值权重反推市场的隐含收益
        self._equilibrium_returns = None  # 初始为None，需要时才计算

    # ==================================================================================
    # 第一部分：添加观点的方法
    # ==================================================================================

    def add_absolute_view(
        self,
        asset: str,
        view_return: float,
        confidence: float = 0.5
    ) -> None:
        """
        添加绝对观点

        什么是绝对观点？
        绝对观点是对某个资产的绝对收益预期。
        例如："平安银行未来一年会涨10%"

        参数：
            asset (str): 资产名称
                - 必须在returns_df的列中
                - 例如：'000001.SZ'

            view_return (float): 预期超额收益（小数形式）
                - 正数表示看涨，负数表示看跌
                - 例如：0.10 表示预期收益10%
                - 例如：-0.05 表示预期收益-5%（下跌）

            confidence (float): 置信度，范围[0, 1]，默认0.5
                - 1.0 表示完全确定
                - 0.5 表示中等确定
                - 0.0 表示完全不确定
                - 例如：0.7 表示70%的信心

        返回：
            None（直接修改self.views）

        异常：
            ValueError: 如果资产不存在或置信度不在[0,1]范围内

        使用示例：
            >>> bl = BlackLittermanEngine(returns_df, market_caps)
            >>> bl.add_absolute_view('000001.SZ', 0.10, confidence=0.7)
            # 添加观点：平安银行涨10%，置信度70%
        """
        # ========== 1. 参数验证 ==========

        # 检查资产是否存在
        if asset not in self.assets:
            raise ValueError(
                f"资产 '{asset}' 不存在。"
                f"可用资产：{self.assets}"
            )

        # 检查置信度范围
        if not (0 <= confidence <= 1):
            raise ValueError(
                f"置信度必须在[0, 1]之间，当前值：{confidence}"
            )

        # 检查收益是否过大（可能输入错误）
        if abs(view_return) > 1:
            warnings.warn(
                f"观点收益 {view_return:.2%} 较大（>100%），"
                f"请确认是否为小数形式（应该用0.10而不是10）"
            )

        # ========== 2. 创建观点字典 ==========

        view = {
            'type': 'absolute',      # 观点类型：绝对观点
            'asset': asset,          # 资产名称
            'return': view_return,   # 预期收益
            'confidence': confidence # 置信度
        }

        # ========== 3. 添加到观点列表 ==========

        self.views.append(view)

        # 清除缓存（因为观点变了，均衡收益需要重新计算）
        self._equilibrium_returns = None

    def add_relative_view(
        self,
        assets: List[str],
        view_returns: List[float],
        confidence: float = 0.5
    ) -> None:
        """
        添加相对观点

        什么是相对观点？
        相对观点是两个资产之间的相对表现预期。
        例如："平安银行会比工商银行好3%"

        参数：
            assets (List[str]): 涉及的两个资产
                - 必须包含2个资产
                - 例如：['000001.SZ', '601398.SH']

            view_returns (List[float]): 相对收益（小数形式）
                - 必须包含2个值
                - 第一个资产的超额收益
                - 第二个资产的超额收益
                - 通常一正一负，和为0
                - 例如：[0.03, -0.03] 表示第一个比第二个好3%

            confidence (float): 置信度，范围[0, 1]，默认0.5

        返回：
            None

        使用示例：
            >>> bl = BlackLittermanEngine(returns_df, market_caps)
            >>> bl.add_relative_view(
            ...     ['000001.SZ', '601398.SH'],
            ...     [0.03, -0.03],
            ...     confidence=0.6
            ... )
            # 添加观点：平安银行比工商银行好3%，置信度60%
        """
        # ========== 1. 参数验证 ==========

        # 检查是否恰好2个资产
        if len(assets) != 2:
            raise ValueError(
                f"相对观点必须恰好包含2个资产，当前：{len(assets)}个"
            )

        # 检查资产是否存在
        for asset in assets:
            if asset not in self.assets:
                raise ValueError(
                    f"资产 '{asset}' 不存在。"
                    f"可用资产：{self.assets}"
                )

        # 检查view_returns
        if len(view_returns) != 2:
            raise ValueError(
                f"相对观点必须恰好包含2个收益值，当前：{len(view_returns)}个"
            )

        # 检查置信度
        if not (0 <= confidence <= 1):
            raise ValueError(
                f"置信度必须在[0, 1]之间，当前值：{confidence}"
            )

        # 检查相对收益是否接近0和（应该互为相反数）
        if not np.isclose(sum(view_returns), 0, atol=0.01):
            warnings.warn(
                f"相对观点的和应该为0，当前：{sum(view_returns):.4f}"
            )

        # ========== 2. 创建观点字典 ==========

        view = {
            'type': 'relative',           # 观点类型：相对观点
            'assets': assets,             # 涉及的资产
            'returns': view_returns,      # 相对收益
            'confidence': confidence      # 置信度
        }

        # ========== 3. 添加到观点列表 ==========

        self.views.append(view)

        # 清除缓存
        self._equilibrium_returns = None

    # ==================================================================================
    # 第二部分：计算方法
    # ==================================================================================

    def _calculate_equilibrium_returns(self) -> pd.Series:
        """
        计算市场均衡收益（隐含收益）

        什么是均衡收益？
        这是BL模型的核心概念：
        - 假设：当前的市场市值权重是均衡状态下的最优权重
        - 反推：如果市值权重是最优的，那么市场隐含的收益是多少？

        数学公式：
            Π = λ × Σ × w_market

        其中：
            Π：均衡收益（我们要求的）
            λ：风险厌恶系数
            Σ：协方差矩阵
            w_market：市值权重

        风险厌恶系数λ的计算：
            λ = (E[R_m] - R_f) / σ_m²

        其中：
            E[R_m]：市场组合的期望收益
            R_f：无风险利率
            σ_m²：市场组合的方差

        返回：
            pd.Series: 均衡收益，索引为资产名称

        注意：
            这是一个私有方法（以_开头），用户不直接调用
            会在compute_weights()时自动调用
        """
        # ========== 1. 如果已经计算过，直接返回 ==========

        # 这是一个缓存机制，避免重复计算
        if self._equilibrium_returns is not None:
            return self._equilibrium_returns

        # ========== 2. 计算市场组合的收益和风险 ==========

        # 将市值权重字典转换为numpy数组（便于矩阵运算）
        w_market = self.market_weights_series.values

        # 计算市场组合的期望收益
        # 公式：E[R_m] = w' × μ
        # 其中w是权重向量，μ是期望收益向量
        # np.dot是向量点积（对应位置相乘再求和）
        market_return = np.dot(w_market, self.expected_returns.values)

        # 计算市场组合的方差
        # 公式：σ_m² = w' × Σ × w
        # 这是投资组合方差的计算公式
        market_var = np.dot(
            w_market.T,
            np.dot(self.cov_matrix.values, w_market)
        )

        # ========== 3. 计算风险厌恶系数λ ==========

        # 公式：λ = (E[R_m] - R_f) / σ_m²
        risk_aversion = (market_return - self.risk_free_rate) / market_var

        # ========== 4. 计算均衡收益Π ==========

        # 公式：Π = λ × Σ × w_market
        equilibrium_returns = risk_aversion * np.dot(
            self.cov_matrix.values,
            w_market
        )

        # 转换为pandas Series，索引为资产名称
        self._equilibrium_returns = pd.Series(
            equilibrium_returns,
            index=self.assets
        )

        return self._equilibrium_returns

    def _build_view_matrices(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        构造观点矩阵P和观点收益向量Q

        什么是P和Q？
        BL模型需要将观点用数学方式表达：
        - P是观点矩阵（Picker矩阵）
        - Q是观点收益向量

        绝对观点的例子：
            观点："股票A涨10%"
            P = [1, 0, 0, ...]  （选中股票A）
            Q = [0.10]          （收益10%）

        相对观点的例子：
            观点："股票A比股票B高3%"
            P = [1, -1, 0, ...] （A减去B）
            Q = [0.03]          （相对收益3%）

        多个观点时：
            P = [[1, 0, 0],    观点1：股票A
                 [0, 1, -1]]   观点2：股票B比股票C
            Q = [0.10, 0.03]

        返回：
            P: 观点矩阵，形状(k, n)，k是观点数，n是资产数
            Q: 观点收益向量，形状(k, )

            如果没有观点，返回(None, None)
        """
        # ========== 1. 如果没有观点，返回None ==========

        if not self.views:
            return None, None

        # ========== 2. 初始化矩阵 ==========

        n_assets = self.n_assets      # 资产数量
        n_views = len(self.views)     # 观点数量

        # P矩阵：k行n列（k个观点，n个资产）
        P = np.zeros((n_views, n_assets))

        # Q向量：k个元素（k个观点的收益）
        Q = np.zeros(n_views)

        # ========== 3. 填充矩阵 ==========

        for i, view in enumerate(self.views):
            if view['type'] == 'absolute':
                # ========== 绝对观点 ==========

                # 找到资产的索引位置
                asset_idx = self.assets.index(view['asset'])

                # P矩阵的第i行，在asset_idx位置设为1
                # 例如：资产1在位置0，则P[0, 0] = 1
                P[i, asset_idx] = 1.0

                # Q向量的第i个元素
                Q[i] = view['return']

            elif view['type'] == 'relative':
                # ========== 相对观点 ==========

                # 获取两个资产
                asset1, asset2 = view['assets']

                # 找到它们的索引位置
                idx1 = self.assets.index(asset1)
                idx2 = self.assets.index(asset2)

                # P矩阵的第i行
                P[i, idx1] = view['returns'][0]   # 第一个资产的系数
                P[i, idx2] = view['returns'][1]   # 第二个资产的系数

                # Q向量（相对观点通常为0）
                Q[i] = 0

        return P, Q

    def _calculate_view_uncertainty(
        self,
        P: np.ndarray
    ) -> np.ndarray:
        """
        计算观点不确定性矩阵Ω

        什么是Ω？
        Ω是一个对角矩阵，表示每个观点的不确定性：
        - 对角线元素：该观点的方差
        - 非对角线元素：0（假设观点之间独立）

        计算公式：
            Ω_ii = (1/confidence - 1) × P_i × Σ × P_i'

        解释：
        - confidence：置信度（0到1）
        - P_i：第i个观点的行向量
        - Σ：协方差矩阵
        - P_i × Σ × P_i'：该观点的方差（不考虑置信度）

        直观理解：
        - confidence = 1 → Ω_ii = 0（完全相信）
        - confidence = 0.5 → Ω_ii = P_i × Σ × P_i'（中等）
        - confidence = 0 → Ω_ii = ∞（完全不信）

        参数：
            P (np.ndarray): 观点矩阵，形状(k, n)

        返回：
            Ω: 观点不确定性矩阵，形状(k, k)，对角矩阵
        """
        # ========== 1. 初始化Ω矩阵 ==========

        n_views = P.shape[0]  # 观点数量
        Omega = np.zeros((n_views, n_views))  # k×k的零矩阵

        # ========== 2. 计算每个观点的不确定性 ==========

        for i, view in enumerate(self.views):
            # 获取该观点的置信度
            confidence = view['confidence']

            # 提取该观点的行向量
            # P[i, :]获取第i行，reshape(1, -1)转为行向量
            p_i = P[i, :].reshape(1, -1)

            # 计算该观点的方差
            # 公式：var = P_i × Σ × P_i'
            # 这是投资组合方差的计算公式
            var_i = np.dot(p_i, np.dot(self.cov_matrix.values, p_i.T))[0, 0]

            # 根据置信度调整
            # 公式：Ω_ii = (1/conf - 1) × var
            Omega[i, i] = var_i * (1 / confidence - 1)

        return Omega

    def _safe_inverse(self, matrix: np.ndarray) -> np.ndarray:
        """
        安全的矩阵求逆

        为什么需要这个方法？
        矩阵求逆在数值上不稳定，可能失败。
        这个方法先尝试普通求逆，失败则用伪逆。

        普通逆 vs 伪逆：
        - 普通逆：要求矩阵必须是方阵且满秩
        - 伪逆：适用于任何矩阵，包括奇异矩阵

        参数：
            matrix (np.ndarray): 要求逆的矩阵

        返回：
            逆矩阵或伪逆矩阵
        """
        try:
            # 尝试普通求逆
            return np.linalg.inv(matrix)
        except np.linalg.LinAlgError:
            # 失败则使用伪逆（Moore-Penrose伪逆）
            warnings.warn("矩阵求逆失败，使用伪逆代替")
            return np.linalg.pinv(matrix)

    def _calculate_posterior_returns(
        self,
        equilibrium_returns: pd.Series,
        P: Optional[np.ndarray],
        Q: Optional[np.ndarray],
        Omega: Optional[np.ndarray]
    ) -> pd.Series:
        """
        计算后验期望收益

        什么是后验收益？
        后验收益 = 综合市场均衡收益 + 投研观点
        这是BL模型的核心输出。

        数学公式（BL模型的核心公式）：
            E[R] = M1^(-1) × M2

        其中：
            M1 = (τΣ)^(-1) + P'Ω^(-1)P
            M2 = (τΣ)^(-1)Π + P'Ω^(-1)Q

        解释：
        - (τΣ)^(-1)Π：市场均衡收益的贡献
        - P'Ω^(-1)Q：投研观点的贡献
        - 两者的权重由τ和Ω决定

        参数：
            equilibrium_returns: 市场均衡收益
            P: 观点矩阵（如果没有观点则为None）
            Q: 观点收益向量（如果没有观点则为None）
            Omega: 观点不确定性矩阵（如果没有观点则为None）

        返回：
            pd.Series: 后验收益，索引为资产名称
        """
        # ========== 1. 计算中间矩阵 ==========

        # 计算τΣ（tau乘以协方差矩阵）
        tau_sigma = self.tau * self.cov_matrix.values

        # 计算(τΣ)^(-1)（tau Sigma的逆）
        tau_sigma_inv = self._safe_inverse(tau_sigma)

        # ========== 2. 如果没有观点，返回均衡收益 ==========

        if P is None:
            return equilibrium_returns

        # ========== 3. 计算观点部分 ==========

        # 计算Ω^(-1)（Omega的逆）
        Omega_inv = self._safe_inverse(Omega)

        # ========== 4. 计算M1 = (τΣ)^(-1) + P'Ω^(-1)P ==========

        # P'是P的转置，P.T在numpy中
        # P'Ω^(-1)P 是一个矩阵乘法
        M1 = tau_sigma_inv + np.dot(P.T, np.dot(Omega_inv, P))

        # ========== 5. 计算M2 = (τΣ)^(-1)Π + P'Ω^(-1)Q ==========

        # (τΣ)^(-1)Π（市场均衡部分）
        M2_market = np.dot(tau_sigma_inv, equilibrium_returns.values)

        # P'Ω^(-1)Q（观点部分）
        M2_views = np.dot(P.T, np.dot(Omega_inv, Q))

        # 相加
        M2 = M2_market + M2_views

        # ========== 6. 求解后验收益 ==========

        # E[R] = M1^(-1) × M2
        M1_inv = self._safe_inverse(M1)
        posterior_returns = np.dot(M1_inv, M2)

        # 转换为pandas Series
        return pd.Series(posterior_returns, index=self.assets)

    def _optimize_weights(
        self,
        expected_returns: pd.Series,
        allow_short: bool = False,
        weight_bounds: Tuple[float, float] = (0, 1)
    ) -> pd.Series:
        """
        基于期望收益优化权重

        这个方法解决均值-方差优化问题：
        - 目标：最大化夏普比率
        - 约束：权重和为1，权重在边界内

        优化问题：
            max (E[R_p] - R_f) / σ_p

        其中：
            E[R_p] = w' × μ（组合收益）
            σ_p = sqrt(w' × Σ × w)（组合波动）

        等价于：
            min -(E[R_p] - R_f) / σ_p
            （最小化负夏普比率）

        参数：
            expected_returns: 期望收益（后验收益）
            allow_short: 是否允许做空（权重可以为负）
            weight_bounds: 权重边界，默认(0, 1)即不允许做空

        返回：
            pd.Series: 最优权重
        """
        # ========== 1. 定义目标函数 ==========

        def neg_sharpe(weights: np.ndarray) -> float:
            """
            负夏普比率（用于最小化）

            因为我们要最大化夏普比率，但优化器是最小化，
            所以取负号。
            """
            # 计算组合收益
            # E[R_p] = w' × μ
            portfolio_return = np.dot(weights, expected_returns.values)

            # 计算组合方差
            # σ_p² = w' × Σ × w
            portfolio_var = np.dot(
                weights.T,
                np.dot(self.cov_matrix.values, weights)
            )
            portfolio_vol = np.sqrt(portfolio_var)

            # 计算夏普比率
            # Sharpe = (E[R_p] - R_f) / σ_p
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol

            # 返回负值（因为我们要最小化）
            return -sharpe

        # ========== 2. 定义约束条件 ==========

        constraints = [
            # 约束1：权重和为1
            # fun是一个函数，输入权重，输出约束值
            # 约束满足时 = 0
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # ========== 3. 定义边界条件 ==========

        if allow_short:
            # 允许做空：没有边界限制
            bounds = None
        else:
            # 不允许做空：每个权重在[0, 1]之间
            # tuple([weight_bounds] * n_assets)生成n个(0, 1)元组
            bounds = tuple([weight_bounds] * self.n_assets)

        # ========== 4. 初始猜测 ==========

        # 从等权开始（每个资产1/n）
        w0 = np.ones(self.n_assets) / self.n_assets

        # ========== 5. 调用优化器 ==========

        result = minimize(
            fun=neg_sharpe,              # 目标函数
            x0=w0,                       # 初始值
            method='SLSQP',              # 优化算法（序列二次规划）
            bounds=bounds,               # 边界
            constraints=constraints,     # 约束
            options={
                'maxiter': 1000,         # 最大迭代次数
                'ftol': 1e-9             # 容差（收敛条件）
            }
        )

        # ========== 6. 检查结果 ==========

        if not result.success:
            raise ValueError(f"优化失败: {result.message}")

        # ========== 7. 返回权重 ==========

        weights = pd.Series(result.x, index=self.assets)
        return weights

    # ==================================================================================
    # 第三部分：公共接口（用户调用的方法）
    # ==================================================================================

    def compute_weights(
        self,
        allow_short: bool = False,
        weight_bounds: Tuple[float, float] = (0, 1)
    ) -> pd.Series:
        """
        计算BL权重（一站式服务）

        这是最主要的方法，包含了完整的BL模型流程：
        1. 计算市场均衡收益
        2. 构造观点矩阵
        3. 计算观点不确定性
        4. 计算后验收益
        5. 优化权重

        参数：
            allow_short: 是否允许做空
            weight_bounds: 权重边界

        返回：
            pd.Series: 最优权重，索引为资产名称

        使用示例：
            >>> bl = BlackLittermanEngine(returns_df, market_caps)
            >>> bl.add_absolute_view('000001.SZ', 0.10, confidence=0.7)
            >>> weights = bl.compute_weights()
            >>> print(weights)
        """
        # ========== 1. 计算市场均衡收益 ==========

        equilibrium_returns = self._calculate_equilibrium_returns()

        # ========== 2. 构造观点矩阵 ==========

        P, Q = self._build_view_matrices()

        # ========== 3. 计算观点不确定性 ==========

        if P is not None:
            Omega = self._calculate_view_uncertainty(P)
        else:
            Omega = None

        # ========== 4. 计算后验收益 ==========

        posterior_returns = self._calculate_posterior_returns(
            equilibrium_returns,
            P,
            Q,
            Omega
        )

        # ========== 5. 优化权重 ==========

        weights = self._optimize_weights(
            posterior_returns,
            allow_short=allow_short,
            weight_bounds=weight_bounds
        )

        return weights

    def get_portfolio_metrics(
        self,
        weights: pd.Series
    ) -> Dict[str, float]:
        """
        计算组合绩效指标

        参数：
            weights: 权重序列

        返回：
            dict: 包含各种指标的字典
                - annual_return: 年化收益
                - annual_volatility: 年化波动
                - sharpe_ratio: 夏普比率
        """
        # 将权重转为numpy数组
        w = weights.values

        # 计算组合收益
        port_return = np.dot(w, self.expected_returns.values)

        # 计算组合波动
        port_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix.values, w)))

        # 计算夏普比率
        sharpe = (port_return - self.risk_free_rate) / port_vol

        return {
            'annual_return': port_return,
            'annual_volatility': port_vol,
            'sharpe_ratio': sharpe
        }

    def compare_with_benchmarks(
        self,
        weights: pd.Series
    ) -> pd.DataFrame:
        """
        对比不同配权方法

        参数：
            weights: BL权重

        返回：
            DataFrame: 对比表格
                - BL权重: 我们计算的结果
                - 市值权重: 市场权重
                - 等权: 每个资产1/n
                - 最小方差: 最小方差组合
                - 风险平价: 风险平价组合
        """
        # 导入权重计算引擎
        from utils.weighting import WeightingEngine

        # 创建权重引擎
        engine = WeightingEngine(self.returns_df)

        # 计算各种权重
        comparisons = {
            'BL权重': weights,
            '市值权重': self.market_weights_series,
            '等权': engine.equal_weight(),
            '最小方差': engine.minimum_variance(),
            '风险平价': engine.risk_parity(),
        }

        return pd.DataFrame(comparisons)


# ==================================================================================
# 使用示例
# ==================================================================================

if __name__ == '__main__':
    """
    这是一个使用示例，演示如何使用BlackLittermanEngine
    """
    print("=" * 60)
    print(" Black-Litterman模型使用示例".center(60))
    print("=" * 60)

    # ========== 1. 创建模拟数据 ==========

    print("\n1. 创建模拟数据...")

    # 创建模拟收益率数据
    np.random.seed(42)  # 设置随机种子，结果可复现

    # 假设有3个资产，1000天的收益率
    n_assets = 3
    n_days = 1000

    # 生成随机收益率
    returns_data = np.random.randn(n_days, n_assets) * 0.02  # 日收益率，标准差2%

    # 转换为DataFrame
    assets = ['股票A', '股票B', '股票C']
    dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
    returns_df = pd.DataFrame(returns_data, index=dates, columns=assets)

    print(f"   创建了{len(assets)}个资产，{len(returns_df)}天的收益率数据")

    # 创建模拟市值数据（单位：亿元）
    market_caps = {
        '股票A': 3000e8,  # 3000亿元
        '股票B': 2000e8,  # 2000亿元
        '股票C': 1000e8,  # 1000亿元
    }

    print(f"   市值：{[(k, v/1e8) for k, v in market_caps.items()]}")

    # ========== 2. 创建BL引擎 ==========

    print("\n2. 创建Black-Litterman引擎...")
    bl = BlackLittermanEngine(
        returns_df=returns_df,
        market_caps=market_caps,
        tau=0.05,
        risk_free_rate=0.03
    )

    print("   ✅ 引擎创建成功")

    # ========== 3. 添加观点 ==========

    print("\n3. 添加投研观点...")

    # 观点1：股票A涨10%
    bl.add_absolute_view('股票A', 0.10, confidence=0.7)
    print("   观点1: 股票A涨10%，置信度70%")

    # 观点2：股票B比股票C好5%
    bl.add_relative_view(['股票B', '股票C'], [0.05, -0.05], confidence=0.6)
    print("   观点2: 股票B比股票C好5%，置信度60%")

    # ========== 4. 计算权重 ==========

    print("\n4. 计算BL权重...")
    weights = bl.compute_weights()

    print("\n最终权重:")
    for asset, weight in weights.items():
        print(f"   {asset}: {weight:.2%}")

    # ========== 5. 对比分析 ==========

    print("\n5. 对比不同配权方法...")
    comparison = bl.compare_with_benchmarks(weights)

    print("\n对比结果:")
    print(comparison.round(4))

    # ========== 6. 组合指标 ==========

    print("\n6. 计算组合指标...")
    metrics = bl.get_portfolio_metrics(weights)

    print(f"\nBL组合指标:")
    print(f"   年化收益: {metrics['annual_return']:.2%}")
    print(f"   年化波动: {metrics['annual_volatility']:.2%}")
    print(f"   夏普比率: {metrics['sharpe_ratio']:.2f}")

    print("\n" + "=" * 60)
    print(" 示例运行完成！".center(60))
    print("=" * 60)
