# Quant Portfolio Rebalancing - Frontend

量化组合再平衡系统前端应用，基于 React + TypeScript + Ant Design 5.x 构建。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Ant Design | 5.x | UI 组件库 |
| ECharts | 5.x | 图表可视化 |
| echarts-for-react | 3.x | ECharts React 封装 |
| Zustand | 4.x | 状态管理 |
| Axios | 1.x | HTTP 请求 |
| Vite | 5.x | 构建工具 |

## 项目结构

```
frontend/
├── index.html                  # HTML 入口
├── package.json                # 依赖配置
├── tsconfig.json               # TypeScript 配置
├── tsconfig.node.json          # Node TypeScript 配置
├── vite.config.ts              # Vite 构建配置
├── README.md                   # 本文件
└── src/
    ├── main.tsx                # React 入口
    ├── App.tsx                 # 主应用组件（步骤导航）
    ├── App.css                 # 全局样式
    ├── types/
    │   └── index.ts            # TypeScript 类型定义
    ├── store/
    │   └── useAppStore.ts      # Zustand 状态管理
    ├── services/
    │   └── api.ts              # API 服务层
    └── components/
        ├── FileUpload/         # 文件上传组件
        │   └── index.tsx
        ├── ConfigPanel/        # 配置面板组件
        │   └── index.tsx
        ├── ResultDisplay/      # 结果展示组件
        │   └── index.tsx
        └── Charts/             # ECharts 图表
            ├── index.ts
            ├── ReturnCurve.tsx  # 净值曲线
            └── DrawdownCurve.tsx # 回撤曲线
```

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

构建产物输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 功能流程

1. **数据上传** - 上传 Excel/CSV 格式的资产价格数据
2. **配权设置** - 选择权重优化方法（等权重/风险平价/最小方差/最大夏普）
3. **交易成本** - 配置各资产的买卖手续费和滑点
4. **回测分析** - 设置回测参数并运行回测
5. **结果导出** - 查看绩效指标、净值曲线、仓位变化，导出 Excel

## API 代理

开发环境通过 Vite proxy 将 `/api` 请求转发到后端：

```
/api/* → http://localhost:8000/api/*
```

如需修改后端地址，请编辑 `vite.config.ts` 中的 `server.proxy` 配置。

## 环境要求

- Node.js >= 18
- npm >= 9
