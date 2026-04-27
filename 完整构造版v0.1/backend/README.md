# 量化配权系统 v1.0 - 后端

基于 FastAPI 构建的量化资产配权与回测分析后端服务。

## 功能

- 📁 **文件上传**: 支持 Excel (.xlsx/.xls) 和 CSV 格式的资产数据文件
- ⚖️ **配权计算**: 等权、风险平价、最小方差、最大夏普 四种配权方法
- 📈 **回测分析**: 静态权重回测 + 滚动配权回测
- 💰 **交易成本**: 支持买卖成本百分比、固定成本、滑点设置
- 🔄 **滚动配权**: 支持累积窗口和固定窗口两种模式
- 💾 **Excel 导出**: 3 Sheet 报告（仓位时间序列、绩效指标、验算页面）

## 快速开始

### 1. 创建虚拟环境

```bash
cd backend
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
# venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 方式一：直接运行（开发模式，支持热重载）
python -m app.main

# 方式二：uvicorn 命令行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式三：生产模式（无热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 查看 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 文件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传资产数据文件 |
| GET  | `/api/assets` | 获取已上传资产列表 |
| GET  | `/api/assets/{file_id}/preview` | 预览资产数据 |
| DELETE | `/api/assets/{file_id}` | 删除已上传资产 |

### 回测分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/backtest` | 运行回测 |
| GET  | `/api/results/{task_id}` | 获取回测结果 |
| DELETE | `/api/results/{task_id}` | 删除回测结果 |

### 导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/export/{task_id}` | 导出 Excel 报告 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/` | 根路径状态检查 |
| GET  | `/api/health` | 健康检查 |

## 工作流程

```
1. POST /api/upload        → 上传资产文件，获取 file_id
2. POST /api/backtest      → 配置回测参数并运行，获取 task_id
3. GET  /api/results/{id}  → 查询回测结果
4. GET  /api/export/{id}   → 下载 Excel 报告
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # 包初始化
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/                 # API 路由
│   │   ├── __init__.py      # 路由注册
│   │   ├── upload.py        # 文件上传
│   │   ├── backtest.py      # 回测分析
│   │   └── export.py        # Excel 导出
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic 模型
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── data_loader.py   # 数据加载
│   │   ├── weighting.py     # 配权引擎
│   │   └── backtest.py      # 回测引擎
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── helpers.py       # 辅助函数
├── requirements.txt
└── README.md
```

## 技术栈

- **FastAPI** 0.104 - 高性能异步 Web 框架
- **Pydantic** 2.5 - 数据验证和序列化
- **pandas** 2.1 - 数据处理
- **numpy** 1.26 - 数值计算
- **scipy** 1.11 - 优化算法（SLSQP）
- **openpyxl** 3.1 - Excel 文件读写
