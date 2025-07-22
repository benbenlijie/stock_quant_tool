# A股连续涨停板股票量化选股系统

这是一个基于PDF策略报告构建的专业A股量化选股系统，实现了完整的后端API服务和前端可视化界面。

## 🚀 项目概述

本系统严格按照《连续涨停板股票量化选股策略调研报告》实现，采用多因子量化模型筛选具有连续涨停潜力的A股股票。

### 核心特性

- **完整策略实现**: 严格按照PDF报告实现量化选股逻辑
- **实时数据更新**: 每日17:00自动数据更新和策略计算
- **RESTful API**: 提供完整的API接口供前端调用
- **专业前端界面**: React + Ant Design构建的现代化管理界面
- **数据存储**: PostgreSQL数据库 + Redis缓存
- **参数调整**: 支持策略参数动态调整和实时重算
- **历史回测**: 支持历史数据回测和风险控制
- **数据导出**: 多格式数据导出功能

## 📊 策略说明

### 核心策略要求

1. **市场情绪监控**: 涨停家数、连板家数、炸板率、题材热度
2. **候选股初筛**: 流通市值<50亿、近90日无三板、非ST、股价<30元
3. **技术形态筛选**: 日内涨幅≥9%、量比>2、换手率≥10%、突破20日新高
4. **筹码集中度**: 计算成本分布熵，要求集中度>0.65且获利盘>0.5
5. **龙虎榜资金**: 游资/机构净买额占比≥10%加分，砸盘席位>5%减分
6. **综合评分**: 量价30% + 筹码25% + 龙虎榜20% + 题材15% + 资金流10%

### 技术架构

- **后端**: Python 3.11 + FastAPI框架
- **数据库**: PostgreSQL + Redis缓存
- **前端**: React 18 + TypeScript + Ant Design 5.x
- **图表**: ECharts + Ant Design Charts
- **数据源**: Tushare API
- **定时任务**: APScheduler

## 🏗️ 项目结构

```
/workspace/
├── backend/                    # 后端服务
│   ├── main.py                # FastAPI应用入口
│   ├── config.py              # 配置管理
│   ├── database/              # 数据库模块
│   │   ├── connection.py      # 数据库连接
│   │   ├── models.py          # 数据模型
│   │   └── operations.py      # 数据库操作
│   ├── services/              # 业务服务
│   │   ├── tushare_client.py  # Tushare API客户端
│   │   ├── strategy_engine.py # 策略计算引擎
│   │   └── scheduler.py       # 定时任务调度
│   ├── routers/              # API路由
│   │   ├── dashboard.py      # 仪表盘API
│   │   ├── stocks.py         # 股票数据API
│   │   ├── strategy.py       # 策略API
│   │   ├── settings.py       # 设置API
│   │   ├── backtest.py       # 回测API
│   │   └── export.py         # 导出API
│   └── utils/                # 工具模块
│       ├── logger.py         # 日志配置
│       └── redis_client.py   # Redis客户端
├── frontend/                  # 前端应用
│   └── stock-selection-frontend/
│       ├── src/
│       │   ├── components/   # 公共组件
│       │   ├── pages/        # 页面组件
│       │   ├── services/     # API服务
│       │   ├── types/        # 类型定义
│       │   ├── utils/        # 工具函数
│       │   └── router/       # 路由配置
│       └── dist/             # 构建输出
├── extract/                  # 提取的文档
├── docs/                     # 项目文档
└── .env                      # 环境配置
```

## 🎯 功能模块

### 1. Dashboard（仪表盘）

- **市场情绪监控**: 红/绿双色仪表盘显示涨停家数、连板家数、炸板率
- **候选股票表格**: 显示今日筛选结果，包含股票代码、名称、所属题材等
- **详情展开**: 点击行展开显示K线迷你图和龙虎榜席位信息
- **实时数据**: 支持日期选择和数据刷新

### 2. Backtest（历史回测）

- **参数设置**: 设置回测时间区间
- **收益分析**: ECharts可视化收益曲线和回撤分析
- **统计指标**: 总收益率、年化收益、最大回撤、夏普比率等
- **历史记录**: 回测结果列表和详细信息

### 3. Settings（参数设置）

- **策略参数**: 滑块调整市值上限、换手率下限等阈值
- **权重配置**: 拖拽调整各因子权重（自动归一化为100%）
- **实时重算**: 参数调整后即时重新计算选股结果
- **风控设置**: 止损比例、最大回撤等风险参数

## 🔧 部署说明

### 在线访问

- **前端应用**: https://sp3i9aw8w59j.space.minimax.io
- **后端API**: 需要启动本地后端服务

### 本地运行

#### 后端服务

```bash
# 安装依赖
cd /workspace/backend
pip install -r requirements.txt

# 启动服务
python main.py
```

#### 前端开发

```bash
# 开发模式
cd /workspace/frontend/stock-selection-frontend
pnpm install
pnpm dev

# 生产构建
pnpm build
```

### 环境配置

确保`.env`文件包含以下配置：

```env
# Tushare API
TUSHARE_TOKEN=your_tushare_token

# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=stock_analysis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 📡 API接口

### 主要接口

- `GET /api/dashboard` - 获取仪表盘数据
- `GET /api/stocks/candidates` - 获取候选股票列表
- `POST /api/strategy/recompute` - 重新计算策略
- `GET /api/backtest` - 历史回测接口
- `POST /api/export` - 数据导出接口
- `GET /api/settings` - 获取/更新策略参数

### API文档

启动后端服务后访问：`http://localhost:8000/docs`

## 📈 数据流程

1. **数据获取**: 通过Tushare API获取股票数据
2. **数据处理**: 计算技术指标和筹码分布
3. **策略筛选**: 多维度过滤和评分
4. **结果存储**: 保存到PostgreSQL数据库
5. **缓存优化**: Redis缓存热点数据
6. **前端展示**: React界面展示结果

## 🎨 UI特性

### 设计理念

- **专业金融界面**: 采用经典的金融数据展示风格
- **响应式设计**: 支持桌面端和移动端适配
- **实时数据**: 支持数据实时刷新和加载状态
- **交互优化**: 表格展开、参数调节、图表缩放等

### 视觉元素

- **涨跌配色**: 红涨绿跌的经典A股配色方案
- **数据可视化**: ECharts图表展示收益曲线
- **状态指示**: 评分等级、情绪指数等直观展示
- **操作反馈**: 加载动画、成功提示、错误处理

## 🔒 风险控制

- **参数验证**: 严格的输入参数验证
- **错误处理**: 完善的异常捕获和用户提示
- **数据校验**: 数据完整性和有效性检查
- **缓存策略**: 合理的缓存时间避免数据延迟

## 📚 使用说明

1. **访问系统**: 打开前端应用地址
2. **查看仪表盘**: 了解当前市场情绪和候选股票
3. **调整参数**: 在设置页面调整策略参数
4. **运行回测**: 在回测页面测试策略效果
5. **导出数据**: 导出筛选结果进行进一步分析

## 🚨 注意事项

- 本系统仅供学习和研究使用，不构成投资建议
- 量化策略存在风险，实际投资需谨慎
- 确保Tushare API有效性和数据准确性
- 建议在充分回测基础上谨慎使用

## 📝 更新日志

### v1.0.0 (2025-01-22)

- ✅ 完成后端API开发
- ✅ 实现完整策略逻辑
- ✅ 构建React前端界面
- ✅ 部署生产环境
- ✅ 完善文档说明

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📄 许可证

本项目仅供学习和研究使用。