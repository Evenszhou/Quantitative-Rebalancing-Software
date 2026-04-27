# 文档索引与目录结构

**最后更新**: 2026-04-27
**维护者**: AI助手

---

## 📁 目录结构

```
D:\D\复权软件\
├── docs/                          # 所有文档（新增）
│   ├── project/                   # 项目管理文档
│   │   ├── PROJECT_PLAN.md       # 项目总体计划
│   │   ├── TASK_CHECKLIST.md     # 任务进度追踪
│   │   ├── QUICK_REFERENCE.md    # AI快速参考
│   │   └── DAILY_SUMMARY.md      # 每日工作总结
│   │
│   ├── technical/                 # 技术文档
│   │   ├── BL_IMPLEMENTATION_PLAN.md        # BL技术方案
│   │   ├── API_DESIGN_UPDATE.md              # API设计文档
│   │   ├── TUSHARE_INTEGRATION_PLAN.md       # Tushare集成方案
│   │   ├── TUSHARE_README.md                  # Tushare使用说明
│   │   ├── BL_MODEL_COMPLETE.md              # BL完成总结
│   │   └── TUSHARE_INTEGRATION_COMPLETE.md    # Tushare完成总结
│   │
│   ├── daily/                     # 每日总结（按日期归档）
│   │   └── 2026-04-27.md         # 今日总结
│   │
│   └── archive/                   # 归档文档
│       ├── README_PLANNING.md    # 早期规划文档
│       └── CONTEXT_SNAPSHOT_*.md # 历史快照
│
├── quant-rebalancing-app-v0.3/    # 当前版本（主开发）
│   ├── app.py                     # Streamlit主程序
│   ├── utils/                     # 工具模块
│   │   ├── bl_portfolio.py       # ✅ BL模型
│   │   ├── tushare_loader.py     # ✅ Tushare数据
│   │   ├── weighting.py          # ✅ 配权算法
│   │   ├── backtest.py           # ✅ 回测引擎
│   │   └── data_loader.py        # ✅ 数据加载
│   ├── tests/                     # 测试文件
│   ├── config/                    # 配置文件
│   └── examples/                  # 示例代码
│
├── quant-rebalancing-app-v0.2/    # 历史版本（归档）
├── quant-rebalancing-app/         # 历史版本（归档）
│
├── 实验数据/                      # 测试数据
├── 输入数据实例_创业板ETF.xlsx     # 示例数据
│
├── 资管配权方法调研报告.docx       # 外部调研报告
├── 第一版配权软件v0.3实验版简报_20260316.docx
├── 第一版配权软件v0.3实验版简要手册_20260316.pdf
├── 量化配权项目规划.md             # 原始项目规划（归档）
│
├── .gitignore                     # Git忽略配置
├── ARCHIVE_INDEX.md               # 本文件：文档索引
└── README.md                      # 项目说明
```

---

## 📚 文档分类说明

### 1. 项目管理文档 (`docs/project/`)

**用途**: 项目进度、计划、追踪
**更新频率**: 每日或任务完成时

| 文档 | 说明 | 更新时机 | 谁来更新 |
|------|------|----------|----------|
| **PROJECT_PLAN.md** | 项目总体计划，包含4个阶段规划 | 每周或里程碑完成时 | AI助手 |
| **TASK_CHECKLIST.md** | 任务进度追踪，checklist形式 | **每日更新** | AI助手+开发者 |
| **QUICK_REFERENCE.md** | AI助手的"记忆卡片"，快速恢复上下文 | 每次重要决策后 | AI助手 |
| **DAILY_SUMMARY.md** | 每日工作总结（当前日） | 每天结束时 | AI助手 |

**规则**:
- ✅ `TASK_CHECKLIST.md` 必须每日更新
- ✅ `QUICK_REFERENCE.md` 在每次对话开始前查看
- ✅ `DAILY_SUMMARY.md` 每天结束时创建/更新
- ✅ 完成重要任务后，移动到 `docs/daily/YYYY-MM-DD.md`

---

### 2. 技术文档 (`docs/technical/`)

**用途**: 技术方案、API设计、实现细节
**更新频率**: 开发过程中或功能完成时

| 文档 | 说明 | 更新时机 | 谁来更新 |
|------|------|----------|----------|
| **BL_IMPLEMENTATION_PLAN.md** | BL模型技术实现方案 | 功能设计完成时 | AI助手 |
| **API_DESIGN_UPDATE.md** | API设计更新记录 | API变更时 | AI助手 |
| **TUSHARE_INTEGRATION_PLAN.md** | Tushare集成技术方案 | 集成设计完成时 | AI助手 |
| **TUSHARE_README.md** | Tushare使用说明 | 集成完成时 | AI助手 |
| **BL_MODEL_COMPLETE.md** | BL模型完成总结 | **功能完成时** | AI助手 |
| **TUSHARE_INTEGRATION_COMPLETE.md** | Tushare集成完成总结 | **功能完成时** | AI助手 |

**规则**:
- ✅ 设计阶段创建对应的PLAN文档
- ✅ 完成功能后创建COMPLETE总结
- ✅ API变更时更新API_DESIGN_UPDATE.md

---

### 3. 每日总结 (`docs/daily/`)

**用途**: 每日工作记录，归档历史
**更新频率**: 每天结束时

**命名规则**: `YYYY-MM-DD.md`

**内容模板**:
```markdown
# 每日工作总结 (YYYY-MM-DD)

## 今日目标
## 已完成任务
## 产出文件
## 测试结果
## 遇到的问题
## 明日计划
```

**规则**:
- ✅ 每天结束时创建
- ✅ 完成Sprint后归档到archive

---

### 4. 归档文档 (`docs/archive/`)

**用途**: 不再活跃但需要保留的文档
**更新频率**: 不再更新

**包含**:
- `README_PLANNING.md` - 早期规划文档
- `CONTEXT_SNAPSHOT_*.md` - 历史快照
- 过期的每日总结

**规则**:
- ✅ 不再需要的文档移动到这里
- ✅ 保留至少3个月

---

## 🔄 文档生命周期

### 阶段1: 创建
- 在 `docs/technical/` 创建技术方案
- 在 `docs/project/` 创建/更新进度文档

### 阶段2: 活跃使用
- **每日更新**: `TASK_CHECKLIST.md`
- **实时更新**: `QUICK_REFERENCE.md`
- **阶段完成**: `DAILY_SUMMARY.md`

### 阶段3: 完成总结
- 在 `docs/technical/` 创建COMPLETE总结
- 更新 `PROJECT_PLAN.md` 里程碑

### 阶段4: 归档
- 移动到 `docs/archive/`
- 或移动到 `docs/daily/YYYY-MM-DD.md`

---

## 📋 当前活跃文档

### 需要每日查看
- [ ] `docs/project/TASK_CHECKLIST.md` - 查看当前任务
- [ ] `docs/project/QUICK_REFERENCE.md` - AI恢复上下文

### 需要每日更新
- [ ] `docs/project/TASK_CHECKLIST.md` - 更新任务进度
- [ ] `docs/project/DAILY_SUMMARY.md` - 记录今日工作

### 需要任务完成时更新
- [ ] `docs/project/PROJECT_PLAN.md` - 里程碑完成
- [ ] `docs/technical/*_COMPLETE.md` - 功能完成总结

---

## 🎯 快速查找指南

### 我想找...

**项目进度**
→ `docs/project/TASK_CHECKLIST.md`

**技术方案**
→ `docs/technical/BL_IMPLEMENTATION_PLAN.md`

**API文档**
→ `docs/technical/API_DESIGN_UPDATE.md`

**今天做了什么**
→ `docs/project/DAILY_SUMMARY.md`

**某个功能怎么用**
→ `docs/technical/*_README.md`

**历史记录**
→ `docs/daily/YYYY-MM-DD.md`

---

## 🔧 维护规则

### AI助手职责
1. **每次对话开始**:
   - 查看 `QUICK_REFERENCE.md`
   - 查看 `TASK_CHECKLIST.md`

2. **完成任务时**:
   - 更新 `TASK_CHECKLIST.md`（打勾）
   - 更新 `QUICK_REFERENCE.md`（状态）

3. **每天结束时**:
   - 创建 `DAILY_SUMMARY.md`
   - 移动到 `docs/daily/` 归档

4. **完成功能时**:
   - 创建 `*_COMPLETE.md` 总结
   - 更新 `PROJECT_PLAN.md`

### 开发者职责
1. **每天开始**:
   - 告知当前任务编号

2. **完成工作**:
   - 告知AI更新文档

---

## 📊 文档统计

### 当前文档数量
- 项目管理: 4个
- 技术文档: 6个
- 每日总结: 1个（当前）
- 归档文档: 2个

### 总计
- **活跃文档**: 11个
- **归档文档**: 2个

---

## ✅ 整理清单

完成整理后的目录结构：

```
✅ docs/project/           - 项目管理文档
✅ docs/technical/         - 技术文档
✅ docs/daily/            - 每日总结
✅ docs/archive/          - 归档文档
✅ ARCHIVE_INDEX.md       - 本索引文件
```

---

**最后更新**: 2026-04-27
**下次整理**: 每周或文件数>20时
