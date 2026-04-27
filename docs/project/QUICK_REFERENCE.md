# 项目快速参考 (AI助手记忆卡片)

**最后更新**: 2026-04-27 (Day 1完成)
**项目**: 量化配权软件 v0.3 → v0.4
**状态**: Sprint 1 已完成 ✅ (100%)

---

## 🌐 全局规则

### 思考和输出规则
- ✅ **使用中文进行思考和分析**
- ✅ **使用中文进行代码注释和文档编写**
- ✅ **技术术语保留英文（如 API, JSON, DataFrame）**
- ✅ **代码变量名使用英文（遵循Python命名规范）**

### 理由
- 主要用户为中文使用者
- 便于理解和沟通
- 符合团队工作习惯

---

## 🎯 项目一句话

为小型买方机构开发实用的投资组合配权工具，支撑投研流程，未来可能商业化。

---

## 👥 团队情况

- **开发**: 1人（研究员兼开发）
- **AI助手**: 辅助编码、方案设计
- **投研**: 有团队，需要工具支撑

---

## 📊 当前状态

### 已完成 (v0.3)
✅ Streamlit MVP
✅ 4种配权方法（等权、风险平价、最小方差、最大夏普）
✅ 回测引擎
✅ 交易成本设置
✅ 滚动配权
✅ Excel导出
✅ Tushare数据源集成（新增）

### 已完成 (v0.4)
✅ Sprint 1 完成 (2026-04-27)
✅ Black-Litterman模型完整实现
✅ Streamlit BL页面
✅ 回测功能集成
✅ Tushare数据源集成

### 进行中 (v0.4)
🔥 Sprint 2 准备
⬜ 投研观点管理增强
⬜ 会议报告生成
⬜ 参数敏感性分析
⬜ 交易指令生成

### Sprint 1 完成总结 (2026-04-27)
✅ Sprint 1 100%完成（原计划2周，实际1天）
✅ BL核心算法实现（900+行，详细注释）
✅ Streamlit页面集成
✅ 回测功能增强
✅ 5个测试用例全部通过
✅ Tushare数据源集成

### 下一步 (Sprint 2)
⬜ 迅投/miniqmt对接
⬜ 风控增强
⬜ 参数优化
⬜ 商业化准备

---

## 🎯 下一个冲刺 (Sprint 2)

**目标**: 投研观点管理增强 + 会议报告生成

**时间**: 预计1-2周

**关键任务**:
1. 观点持久化存储
2. PDF报告生成
3. 参数敏感性分析

---

## 🛠️ 技术栈

### 核心
```yaml
语言: Python 3.10+
框架: Streamlit (不改为FastAPI+React)
数据: Pandas, NumPy
优化: SciPy
存储: JSON文件 (不用PostgreSQL)
日志: 标准logging
```

### 目录结构
```
quant-rebalancing-app-v0.3/
├── app.py                      # Streamlit主程序
├── utils/
│   ├── data_loader.py          # ✅ 已有
│   ├── weighting.py            # ✅ 已有
│   ├── backtest.py             # ✅ 已有
│   ├── tushare_loader.py       # ✅ 已完成
│   ├── bl_portfolio.py         # ✅ 已完成
│   ├── order_generator.py      # ⬜ 待做
│   ├── sensitivity_analysis.py # ⬜ 待做
│   └── report_generator.py     # ⬜ 待做
├── config/
│   ├── tushare.yaml            # ✅ 新增
│   ├── views.json              # 观点存储
│   └── parameters.json         # 参数配置
├── examples/
│   └── tushare_example.py      # ✅ 新增
└── tests/
```

---

## 📋 Black-Litterman实现清单

### 核心类和方法
```python
class BlackLittermanEngine:
    def __init__(self, returns_df, market_caps, tau=0.05):
        """初始化引擎"""

    def calculate_equilibrium_returns(self):
        """计算市场均衡收益 Π"""

    def add_view(self, assets, view_returns, confidence):
        """添加观点"""

    def compute_posterior_returns(self):
        """计算后验收益 E[R]"""

    def optimize_weights(self):
        """基于后验收益优化权重"""

    def get_portfolio_metrics(self, weights):
        """计算组合指标"""
```

### 关键公式
```
均衡收益: Π = λ Σ w_market
后验收益: E[R] = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) [(τΣ)^(-1)Π + P'Ω^(-1)Q]
```

### 参数
- **tau (τ)**: 0.01-0.05，通常0.05
- **P**: 观点矩阵
- **Q**: 观点收益向量
- **Ω**: 观点不确定性矩阵

---

## 🎯 界面设计

### 新页面结构
```
6. 投研观点管理
   ├─ 观点录入表单
   ├─ 观点列表
   └─ BL配权结果

7. 交易指令生成
   ├─ 导入当前持仓
   ├─ 导入目标权重
   └─ 生成调仓指令

8. 参数敏感性分析
   ├─ 参数选择
   ├─ 批量回测
   └─ 结果可视化
```

---

## 🚫 明确不做

❌ 机器学习/深度学习（黑箱、过拟合）
❌ 复杂工程化（K8s、微服务）
❌ 前后端分离（1人维护不起）
❌ 17种方法全做（维护成本高）
❌ PostgreSQL（JSON够用）

---

## ✅ 验收标准

### BL模型
- [ ] 能输入观点（资产、预期收益、置信度）
- [ ] 能计算BL权重
- [ ] 能对比：BL vs 等权 vs 市场权重
- [ ] 单元测试覆盖率 > 80%
- [ ] 通过历史数据回测验证

### 投研观点管理
- [ ] CRUD功能完整
- [ ] JSON存储正常工作
- [ ] 支持导入导出

### 会议报告
- [ ] PDF格式专业
- [ ] 包含所有必要信息
- [ ] 一键生成

---

## 📚 参考资料

### 理论文档
- [Idzorek (2007) - BL Step-by-Step](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1413550)
- [PyPortfolioOpt文档](https://pyportfolioopt.readthedocs.io/)

### 代码参考
- PyPortfolioOpt的BL实现
- 开源的BL模型示例

---

## 🔍 快速检查点

### 每日开始工作时
1. 查看 `QUICK_REFERENCE.md`（本文件），回顾关键信息
2. 查看 `TASK_CHECKLIST.md`，确认当前任务
3. 检查是否有阻塞问题

### 每日结束时
1. 更新 `TASK_CHECKLIST.md` 进度
2. 更新 `工作日志.md`，记录今日产出
3. 规划第二天任务

---

## 💬 重要决策记录

### 为什么选BL模型？
1. 直接支撑投研流程（研究员有观点）
2. 可解释性强（IC能看懂）
3. 业界标准，不是黑箱
4. 商业化时的卖点

### 为什么不用PostgreSQL？
1. 数据量不大（观点数量有限）
2. JSON文件简单，便于调试
3. 需要时随时迁移

### 为什么保持Streamlit？
1. 1人开发，维护不起前后端分离
2. Streamlit够用，内部工具UI不重要
3. 快速迭代

---

## 🎯 本周目标 (Week 1: 4/27-5/03)

**主要目标**: 完成BL核心算法

**周一-周二**: 理论准备
**周三-周四**: 算法实现
**周五**: 测试验证

**预期产出**:
- utils/bl_portfolio.py
- tests/test_bl_portfolio.py
- 通过单元测试

---

## 📞 联系和协作

- 开发者: 1人，研究员兼开发
- AI助手: 辅助编码、方案设计、问题解决
- 沟通方式: 直接在代码中讨论，文档化决策

---

## 🔄 下一步行动

**立即行动**:
1. 开始BL理论学习和研究
2. 设计API接口
3. 开始编码核心算法

**本周内**:
1. 完成核心算法实现
2. 完成单元测试
3. 准备Streamlit集成

**下周**:
1. Streamlit界面开发
2. 投研观点管理
3. 开始报告生成

---

**备注**: 这是我（AI助手）的快速记忆卡片，每次对话前先review，保持上下文一致。
