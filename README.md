# 量化配权软件

**版本**: v0.3 → v0.4 (开发中)
**最后更新**: 2026-04-27
**项目类型**: 买方投资机构内部工具（可能商业化）

---

## 📖 项目简介

为小型买方机构开发的投资组合配权工具，支撑投研决策流程。

**核心功能**：
- ✅ 多种配权方法（等权、风险平价、最小方差、最大夏普）
- ✅ Black-Litterman模型（融合投研观点）
- ✅ 回测分析和交易成本计算
- ✅ Tushare数据源集成
- ⏳ 投研观点管理（开发中）
- ⏳ 会议报告生成（开发中）

---

## 🚀 快速开始

### 1. 项目结构

```
量化配权软件/
├── docs/                          # 📚 所有文档
│   ├── project/                   # 项目管理
│   ├── technical/                 # 技术文档
│   └── daily/                     # 每日总结
├── quant-rebalancing-app-v0.3/    # 💻 当前版本
└── ARCHIVE_INDEX.md               # 📑 文档索引（重要！）
```

### 2. 查看文档索引

**新用户必看**：
```bash
1. 查看 ARCHIVE_INDEX.md - 了解文档结构和位置
2. 查看 docs/PROJECT_PLAN.md - 了解项目总体计划
3. 查看 docs/project/TASK_CHECKLIST.md - 查看当前任务
```

### 3. 运行软件

```bash
cd quant-rebalancing-app-v0.3
streamlit run app.py
```

---

## 📊 开发进度

### 当前版本：v0.3 ✅
- 4种配权方法
- 回测引擎
- 交易成本设置
- Excel导出

### 开发中：v0.4 🚧
- ✅ Black-Litterman模型核心算法
- ✅ Tushare数据源集成
- ⏳ Streamlit界面集成
- ⏳ 投研观点管理
- ⏳ 会议报告生成

**详细进度**: 见 `docs/project/TASK_CHECKLIST.md`

---

## 📚 文档导航

### 🔥 必读文档

| 文档 | 用途 | 位置 |
|------|------|------|
| **ARCHIVE_INDEX.md** | 文档索引和目录结构 | 根目录 |
| **PROJECT_PLAN.md** | 项目总体计划 | docs/project/ |
| **TASK_CHECKLIST.md** | 任务进度追踪 | docs/project/ |
| **QUICK_REFERENCE.md** | AI快速参考 | docs/project/ |

### 📖 技术文档

| 文档 | 说明 | 位置 |
|------|------|------|
| **BL_IMPLEMENTATION_PLAN.md** | BL模型技术方案 | docs/technical/ |
| **TUSHARE_INTEGRATION_PLAN.md** | Tushare集成方案 | docs/technical/ |
| **TUSHARE_README.md** | Tushare使用说明 | docs/technical/ |

### 📝 每日记录

| 文档 | 说明 | 位置 |
|------|------|------|
| **DAILY_SUMMARY.md** | 当前日总结 | docs/project/ |
| **YYYY-MM-DD.md** | 历史每日总结 | docs/daily/ |

---

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **框架**: Streamlit
- **核心库**: Pandas, NumPy, SciPy
- **数据源**: Tushare Pro
- **存储**: JSON文件（不用数据库）

---

## 📋 文档更新规则

**重要**：文档管理规则见 `docs/DOCUMENTATION_RULES.md`

**每日必做**：
1. 更新 `docs/project/TASK_CHECKLIST.md`
2. 更新 `docs/project/DAILY_SUMMARY.md`

**每次对话开始**：
- 查看 `docs/project/QUICK_REFERENCE.md`

---

## 🎯 项目阶段

### Phase 1: 支撑投研流程 (Month 1) 🚧
**目标**: 完成BL模型和投研观点管理

**进度**: 82.6%
- ✅ BL模型核心算法
- ✅ Tushare数据源
- ⏳ Streamlit集成

### Phase 2: 实盘对接准备 (Month 2-3)
- 迅投/miniqmt对接
- 风控增强

### Phase 3: 功能增强 (Month 4-6)
- 参数优化
- 更多配权方法

### Phase 4: 商业化准备 (Month 6+)
- 多用户系统
- 云部署

---

## 👥 团队

- **开发**: 1人（研究员兼开发）
- **AI助手**: 辅助编码和方案设计

---

## 📞 获取帮助

1. **查看文档索引**: `ARCHIVE_INDEX.md`
2. **查看更新规则**: `docs/DOCUMENTATION_RULES.md`
3. **查看技术方案**: `docs/technical/`

---

## 📄 许可证

内部使用，未来可能商业化。

---

**最后更新**: 2026-04-27
**维护者**: AI助手
**项目状态**: 活跃开发中
