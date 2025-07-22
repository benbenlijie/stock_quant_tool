# A股量化选股系统前端

基于React 18 + TypeScript + Ant Design 5.x构建的现代化量化选股系统前端界面。

## 🚀 在线访问

**部署地址**: https://sp3i9aw8w59j.space.minimax.io

## 📱 功能特性

### 🎯 核心页面

1. **Dashboard（仪表盘）**
   - 市场情绪仪表盘（涨停家数、连板家数、炸板率）
   - 今日候选股票表格展示
   - 行点击展开：K线迷你图 + 龙虎榜席位
   - 实时数据刷新和日期选择

2. **Backtest（历史回测）**
   - 区间回测参数设置
   - 收益/回撤图表可视化
   - 回测结果统计和历史记录

3. **Settings（参数设置）**
   - 策略参数滑块调整
   - 权重拖拽配置（自动归一化）
   - 实时重算功能

### 🎨 UI/UX特性

- **专业金融界面**: 经典红涨绿跌配色
- **响应式设计**: 完美适配桌面和移动端
- **实时交互**: 数据刷新、加载状态、错误处理
- **数据可视化**: ECharts图表、进度条、统计卡片
- **操作优化**: 表格展开、参数调节、一键导出

## 🛠️ 技术栈

- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **图表**: ECharts for React
- **HTTP**: Axios
- **路由**: React Router v6
- **日期**: Day.js
- **构建**: Vite
- **包管理**: pnpm

## 📦 项目结构

```
src/
├── components/          # 公共组件
│   ├── Layout/         # 主布局组件
│   ├── StockTable/     # 股票表格组件
│   └── MarketSentiment/# 市场情绪组件
├── pages/              # 页面组件
│   ├── Dashboard/      # 仪表盘页面
│   ├── Backtest/       # 回测页面
│   └── Settings/       # 设置页面
├── services/           # API服务
│   └── api.ts         # API接口封装
├── types/              # 类型定义
│   └── index.ts       # 全局类型
├── utils/              # 工具函数
│   └── index.ts       # 通用工具
├── router/             # 路由配置
│   └── index.tsx      # 路由定义
├── App.tsx            # 主应用组件
└── main.tsx           # 应用入口
```

## 🚀 快速开始

### 安装依赖

```bash
pnpm install
```

### 开发模式

```bash
pnpm dev
```

### 生产构建

```bash
pnpm build
```

### 预览构建

```bash
pnpm preview
```

## ⚙️ 环境配置

### API地址配置

在`src/services/api.ts`中配置后端API地址：

```typescript
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:8000/api',
  timeout: 30000
});
```

### 开发环境

确保后端服务已启动在`http://localhost:8000`

## 📱 页面详情

### Dashboard 仪表盘

- **市场情绪监控**
  - 情绪指数仪表盘
  - 涨停家数统计
  - 连板分布情况
  - 炸板率分析

- **候选股票表格**
  - 股票基本信息
  - 技术指标展示
  - 综合评分排名
  - 详情展开查看

- **操作功能**
  - 日期选择器
  - 数据刷新
  - 策略重算
  - 结果导出

### Backtest 历史回测

- **参数设置**
  - 回测时间区间选择
  - 策略参数配置

- **结果展示**
  - 收益曲线图表
  - 关键指标统计
  - 历史回测记录

### Settings 参数设置

- **基础筛选参数**
  - 市值上限滑块
  - 换手率下限
  - 量比阈值
  - 涨幅要求

- **策略权重配置**
  - 各因子权重调整
  - 自动归一化
  - 权重分布可视化

- **风控参数**
  - 止损比例
  - 最大回撤
  - 最大仓位

## 🎨 样式定制

### 主题配置

在`App.tsx`中配置Ant Design主题：

```typescript
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
    },
    components: {
      Layout: {
        siderBg: '#001529',
      },
    },
  }}
>
```

### 响应式断点

- **xs**: < 576px（手机）
- **sm**: ≥ 576px（小屏平板）
- **md**: ≥ 768px（平板）
- **lg**: ≥ 992px（桌面）
- **xl**: ≥ 1200px（大屏桌面）

## 🔧 开发指南

### 添加新页面

1. 在`src/pages/`下创建页面组件
2. 在`src/router/index.tsx`中添加路由
3. 在布局组件中添加菜单项

### API接口调用

```typescript
import apiService from '../services/api';

// 获取仪表盘数据
const data = await apiService.getDashboard();

// 错误处理已在拦截器中统一处理
```

### 类型定义

所有数据类型定义在`src/types/index.ts`中，确保类型安全。

## 📊 性能优化

- **代码分割**: 使用React.lazy进行路由级别的代码分割
- **防抖节流**: 对频繁操作进行防抖处理
- **虚拟滚动**: 大量数据表格使用虚拟滚动
- **缓存策略**: API响应数据合理缓存

## 🐛 错误处理

- **全局错误边界**: 捕获组件渲染错误
- **API错误处理**: 统一的错误提示和重试机制
- **表单验证**: 完善的输入验证和提示
- **网络状态**: 网络异常提示和重连

## 📱 移动端适配

- **响应式布局**: 使用Ant Design的栅格系统
- **触摸优化**: 移动端手势和触摸优化
- **性能优化**: 移动端性能和体验优化

## 🚀 部署

### 构建配置

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    chunkSizeWarningLimit: 1000,
  },
});
```

### 生产部署

1. 执行`pnpm build`构建项目
2. 将`dist`目录部署到静态文件服务器
3. 配置Nginx反向代理API请求

## 🔒 安全考虑

- **输入验证**: 所有用户输入进行验证
- **XSS防护**: 避免innerHTML等危险操作
- **CSRF保护**: API请求添加CSRF Token
- **权限控制**: 基于角色的访问控制

## 📈 监控和分析

- **错误监控**: 集成错误监控服务
- **性能监控**: 页面加载和交互性能
- **用户行为**: 用户操作和使用习惯分析

## 🎯 未来规划

- [ ] 实时数据推送（WebSocket）
- [ ] 更多图表类型和自定义配置
- [ ] 暗色主题支持
- [ ] 移动端原生应用
- [ ] 更多导出格式支持

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目仅供学习和研究使用。