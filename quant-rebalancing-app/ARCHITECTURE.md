# 配权软件代码分层架构文档

## 📚 依赖关系总览

```
┌─────────────────────────────────────────────────────────────┐
│                        Layer 4: 应用层                        │
│                         app.py                               │
│              (Streamlit Web界面，调用所有底层模块)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼──────┐
│   Layer 3:     │           │   Layer 3:    │
│   backtest.py  │           │  (未来扩展)    │
│  (回测引擎)     │           │               │
│  依赖: Layer 2 │           │               │
└───────┬────────┘           └───────────────┘
        │
        │
┌───────▼────────┐
│   Layer 2:     │
│  weighting.py  │
│  (配权算法)     │
│  依赖: Layer 1 │
└───────┬────────┘
        │
        │
┌───────▼────────┐
│   Layer 1:     │
│ data_loader.py │
│ (数据加载)      │
│ 只依赖外部库    │
└────────────────┘
```

---

## 🏗️ Layer 1: 基础数据层 (data_loader.py)

### 📌 模块职责
**最底层，负责和外部世界打交道：**
- 读取Excel/CSV文件
- 清洗数据
- 准备收益率数据
- 验证数据质量

### 📦 类：DataLoader

#### 属性（Layer 1）

**`self.date_columns: list`**
- **作用**: 日期列的候选名单
- **示例**: ['日期', 'date', 'Date', '时间']
- **新手教学**: 系统会尝试在这些列名中找日期，就像你告诉Excel"日期"、"时间"都是时间列

**`self.price_columns: dict`**
- **作用**: 价格列的候选名单（字典格式）
- **示例**: `{'close': ['收盘价', 'close', 'Close'], 'open': ['开盘价', 'open']}`
- **新手教学**: 告诉系统"收盘价"、"close"都对应标准名'close'，方便统一处理

#### 方法（Layer 1）

**`load_file(file_obj) -> pd.DataFrame`**
- **依赖**: pandas.read_excel(), pandas.read_csv()
- **功能**: 读取文件，标准化列名，处理日期
- **新手教学**: 就像在Excel里"文件→打开"，系统自动识别格式并整理

**`prepare_returns(assets_data) -> pd.DataFrame`**
- **依赖**: numpy.log(), pandas.pct_change()
- **功能**: 从价格计算收益率
- **新手教学**: 
  - 简单收益率 = (今天价格 - 昨天价格) / 昨天价格
  - 对数收益率 = ln(今天价格 / 昨天价格)
  - 为什么要收益率？因为不同资产价格不同（创业板100元，沪深300200元），无法直接比较，但收益率可以

**`validate_data(df) -> dict`**
- **依赖**: pandas.isnull()
- **功能**: 检查数据质量
- **新手教学**: 就像考试前检查：必需的列有了吗？数据够吗？有没有缺失？

---

## ⚖️ Layer 2: 配权计算层 (weighting.py)

### 📌 模块职责
**中间层，根据Layer 1准备的收益率数据，计算最优权重**

### 📦 类：WeightingEngine

#### 初始化依赖（Layer 2）

**`__init__(returns_df: pd.DataFrame)`**
- **输入**: Layer 1的DataLoader.prepare_returns()输出的收益率数据
- **计算**: 
  - 协方差矩阵（衡量资产间相关性）
  - 期望收益率（年化）
  - 波动率（年化）
- **新手教学**: 
  - 协方差矩阵：衡量两个资产"一起涨一起跌"的程度
  - 期望收益率：历史平均收益（年化）
  - 波动率：价格波动的剧烈程度（年化标准差）

#### 方法（Layer 2）

**`equal_weight() -> pd.Series`**
- **依赖**: 无（纯数学计算）
- **功能**: 每个资产权重相等
- **示例**: 3个资产 → [1/3, 1/3, 1/3]
- **新手教学**: 最简单的配权方法，就像平均分蛋糕

**`risk_parity() -> pd.Series`**
- **依赖**: scipy.optimize.minimize() + Layer 2属性（协方差矩阵）
- **功能**: 每个资产对组合总风险的贡献相等
- **数学原理**: 
  1. 计算每个资产的边际风险贡献
  2. 调整权重，使每个资产的风险贡献相等
- **新手教学**: 
  - 不是平均分钱，而是平均分"风险"
  - 高波动资产（如创业板）少配，低波动资产（如债券）多配
  - 目的：组合不会因为某个资产剧烈波动而大幅震荡

**`minimum_variance() -> pd.Series`**
- **依赖**: scipy.optimize.minimize() + Layer 2属性（协方差矩阵）
- **功能**: 最小化组合方差（波动率）
- **数学原理**: 在所有可能的权重组合中，找到方差最小的那个
- **新手教学**: 
  - 目标：组合波动最小，最稳定
  - 缺点：可能错过高收益资产
  - 适合：保守型投资者

**`maximum_sharpe() -> pd.Series`**
- **依赖**: scipy.optimize.minimize() + Layer 2属性（协方差矩阵、期望收益率）
- **功能**: 最大化夏普比率（风险调整后收益）
- **数学原理**: 夏普比率 = (收益率 - 无风险利率) / 波动率
- **新手教学**: 
  - 不是追求收益最高，也不是风险最低
  - 而是追求"单位风险下的收益最高"
  - 适合：理性投资者

**`get_portfolio_metrics(weights) -> dict`**
- **依赖**: Layer 2属性（期望收益率、协方差矩阵）
- **功能**: 计算组合的绩效指标
- **输出**: 年化收益率、年化波动率、夏普比率、风险贡献
- **新手教学**: 评估一个组合好不好的关键指标

---

## 📈 Layer 3: 回测分析层 (backtest.py)

### 📌 模块职责
**高层，根据Layer 2的权重，进行历史回测**

### 📦 类：BacktestEngine

#### 初始化依赖（Layer 3）

**`__init__(returns_df, weights, baseline_asset)`**
- **输入**: 
  - returns_df: Layer 1的收益率数据
  - weights: Layer 2的权重结果
  - baseline_asset: 基准资产名
- **新手教学**: 准备回测的三要素：历史数据、策略权重、对比基准

#### 方法（Layer 3）

**`run_backtest(initial_value, rebalance_freq) -> dict`**
- **依赖**: 
  - Layer 3内部方法：_buy_and_hold(), _rebalance_periodically()
  - Layer 3内部方法：_calculate_metrics(), _calculate_drawdown()
- **功能**: 
  1. 根据权重进行历史回测
  2. 计算组合收益率曲线
  3. 与基准对比
  4. 计算绩效指标
- **新手教学**: 
  - 就像用历史数据"彩排"一遍策略
  - 假设在2020年买入，按月调整仓位，看看现在赚了多少
  - 与基准对比：看策略是否跑赢简单的"买入持有"

**`_buy_and_hold(returns, weights) -> pd.Series`**
- **依赖**: pandas矩阵运算
- **功能**: 买入持有策略（不调仓）
- **新手教学**: 
  - 一开始分配好权重后，就不再调整
  - 随着资产涨跌，权重会自然偏离
  - 优点：交易成本低；缺点：权重会偏离目标

**`_rebalance_periodically(returns, weights, freq) -> pd.Series`**
- **依赖**: pandas.resample()
- **功能**: 定期再平衡（月度/季度/年度）
- **新手教学**: 
  - 每月/季度调整仓位，恢复到目标权重
  - 比如：目标是创业板30%，但涨到40%了，就卖出10%
  - 优点：保持目标配置；缺点：交易成本高

**`_calculate_metrics(portfolio_returns, baseline_returns) -> dict`**
- **依赖**: numpy统计函数
- **功能**: 计算绩效指标
- **输出**:
  - 年化收益率: (1+日收益)^252 - 1
  - 年化波动率: 日波动率 × √252
  - 夏普比率: (收益率-无风险利率) / 波动率
  - 最大回撤: 从最高点跌到最低点的幅度
  - Calmar比率: 年化收益 / 最大回撤
  - 信息比率: 超额收益 / 跟踪误差
  - 胜率: 跑赢基准的天数占比
- **新手教学**: 
  - 年化收益率：平均每年赚多少
  - 夏普比率：单位风险的收益，越高越好（>1算好，>2很好）
  - 最大回撤：最惨的时候亏多少（负数，-10%表示最多亏10%）
  - 胜率：有多少天跑赢基准

**`_calculate_drawdown(cumulative_returns) -> pd.Series`**
- **依赖**: pandas.cummax()
- **功能**: 计算回撤序列
- **新手教学**: 
  - 回撤 = (当前净值 - 历史最高净值) / 历史最高净值
  - 总是负数或0
  - 最大回撤是最小的那个值（比如-15%）

---

## 🎯 Layer 4: 应用层 (app.py)

### 📌 模块职责
**最上层，用户界面，调用所有底层模块**

### 依赖关系（Layer 4）

**导入Layer 1-3:**
```python
from utils.data_loader import DataLoader
from utils.weighting import WeightingEngine
from utils.backtest import BacktestEngine
```

**调用流程:**
1. 用户上传文件 → DataLoader.load_file() → 数据预览
2. 用户选择配权方法 → WeightingEngine.risk_parity() → 权重结果
3. 用户点击回测 → BacktestEngine.run_backtest() → 绩效指标和图表

### 新手教学

**Streamlit是什么？**
- 一个Python Web框架，专门用于数据科学应用
- 优点：不用写HTML/CSS/JavaScript，纯Python就能做网页
- 类比：就像是"数据科学的PowerPoint"，拖拖拽拽就能做出交互式报表

**app.py的工作流程:**
1. 用streamlit.file_uploader()让用户上传文件
2. 调用DataLoader读取数据
3. 用户选择配权方法，调用WeightingEngine计算权重
4. 用户点击回测，调用BacktestEngine计算绩效
5. 用plotly画图，用streamlit.plotly_chart()显示

---

## 🔬 数学公式总结

### Layer 1: 数据处理
- **简单收益率**: r_t = (P_t - P_{t-1}) / P_{t-1}
- **对数收益率**: r_t = ln(P_t / P_{t-1})

### Layer 2: 配权计算
- **协方差矩阵**: Σ = Cov(R_i, R_j)
- **组合收益率**: R_p = Σ w_i R_i
- **组合方差**: σ²_p = w' Σ w
- **夏普比率**: SR = (E[R_p] - R_f) / σ_p

### Layer 3: 回测分析
- **年化收益率**: (1 + r_daily)^252 - 1
- **年化波动率**: σ_daily × √252
- **最大回撤**: max(Peak - Current) / Peak
- **信息比率**: (R_p - R_b) / σ(R_p - R_b)

---

## 📖 新手快速上手指南

### 第一步：理解数据流
```
用户上传文件
    ↓
DataLoader读取并清洗 (Layer 1)
    ↓
WeightingEngine计算权重 (Layer 2)
    ↓
BacktestEngine进行回测 (Layer 3)
    ↓
Streamlit展示结果 (Layer 4)
```

### 第二步：运行示例
```bash
cd quant-rebalancing-app
streamlit run app.py
```

### 第三步：阅读代码顺序
1. 先看 `data_loader.py` - 理解数据怎么读进来的
2. 再看 `weighting.py` - 理解权重怎么算出来的
3. 然后看 `backtest.py` - 理解回测怎么做的
4. 最后看 `app.py` - 理解界面怎么把这些串起来

### 第四步：修改和扩展
想加新功能？
- 加新的配权方法 → 修改 `weighting.py`
- 加新的绩效指标 → 修改 `backtest.py`
- 加新的数据格式 → 修改 `data_loader.py`
- 修改界面布局 → 修改 `app.py`

---

## 🎓 进阶学习路径

### Level 1: 使用者
- 会运行软件
- 会调整参数
- 会解读结果

### Level 2: 修改者
- 会修改配权算法
- 会添加新的绩效指标
- 会优化代码性能

### Level 3: 开发者
- 会设计新的模块
- 会重构架构
- 会添加新功能

---

**文档版本:** V1.0  
**最后更新:** 2026-03-09  
**维护者:** 小雅(AI研究助手)
