# A股连续涨停板股票量化选股系统开发计划

## 项目目标
构建一个基于PDF策略报告的A股量化选股网站系统，每日自动调用Tushare API进行数据更新和候选股筛选，为用户提供可视化界面展示选股结果、历史回测和风险控制。

## 核心策略要求（基于PDF报告）
1. **市场情绪监控**：涨停家数、连板家数、炸板率、题材热度
2. **候选股初筛**：流通市值<50亿、近90日无三板、非ST、股价<30元
3. **技术形态筛选**：日内涨幅≥9%、量比>2、换手率≥10%、突破20日新高
4. **筹码集中度**：计算成本分布熵，要求集中度>0.65且获利盘>0.5
5. **龙虎榜资金**：游资/机构净买额占比≥10%加分，砸盘席位>5%减分
6. **综合评分**：量价30% + 筹码25% + 龙虎榜20% + 题材15% + 资金流10%

## 技术架构
- **后端**：Python 3.11 + FastAPI + APScheduler + Redis
- **数据库**：PostgreSQL（行情快照、回测记录）
- **前端**：React + Ant Design + ECharts
- **部署**：Docker Compose + Nginx
- **CI/CD**：GitHub Actions

## 执行步骤

### [✅] STEP 1: 研究Tushare API接口并验证核心数据获取能力 -> Research STEP
- 验证策略所需的关键API接口可用性和数据质量
- 研究limit_list_d, daily_basic, stk_limit, top_list, top_inst等核心接口
- 制定数据获取和存储方案

### [✅] STEP 2: 获取Tushare Token并进行环境配置 -> System STEP  
- 向用户获取Tushare Pro API Token
- 配置开发环境和数据库连接

### [✅] STEP 3: 构建量化选股系统后端核心功能 -> Web Development STEP
- 实现PDF报告中描述的完整选股策略逻辑
- 开发数据采集、指标计算、筛选评分等核心模块
- 搭建FastAPI后端服务和定时任务调度
- 集成PostgreSQL数据存储和Redis缓存

### [✅] STEP 4: 开发前端可视化界面 -> Web Development STEP  
- 构建Dashboard（情绪仪表盘+选股结果表格）
- 实现Backtest回测功能（参数表单+收益回撤图）
- 开发Settings参数调整界面（阈值滑块、权重设置）
- 集成K线图、龙虎榜数据展示等交互功能

### [✅] STEP 5: 系统部署和运维配置 -> Web Development STEP
- 配置Docker Compose部署方案
- 设置GitHub Actions CI/CD流水线  
- 完善监控、日志和错误处理机制
- 编写技术文档和使用指南

## 最终交付物
1. **完整的Git仓库**：包含所有源代码、配置文件和文档
2. **可运行的Web应用**：本地或云端部署的完整系统
3. **技术文档**：README、API文档、部署指南
4. **策略流程图**：Mermaid格式的选股流程可视化
5. **单元测试**：覆盖率≥80%的测试用例

## 关键特性
- ✅ 严格按照PDF策略报告实现选股逻辑
- ✅ 每日17:00自动数据更新和选股计算  
- ✅ 交互式参数调整和实时重算
- ✅ 可视化Dashboard和历史回测
- ✅ 一键导出CSV/Excel功能
- ✅ 完整的风控和止损机制
- ✅ Docker容器化部署方案
