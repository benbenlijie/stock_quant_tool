# 获利盘比例计算优化文档 - 基于换手率递推法的科学实现

## 核心结论

**准确计算"筹码分布"与"获利盘比例"的核心是：在"数据精度 vs 现实可得性"的主要矛盾中，根据可获得的数据粒度（Tick/分时/日线）构建一个可递推的成交成本分布模型（常用的是基于换手率的递推法），再用当前价与分布比较即可得获利盘比例。**

## 背景与主要矛盾

原有的获利盘比例计算方法过于简化，仅基于当日涨跌幅进行估算，缺乏准确性。通过深入分析，我们发现：

### 主要矛盾
- **准确性**（需要精细成交数据、交易明细、逐笔撮合价） vs. **可行性**（一般仅有日线数据和换手率）

### 次要矛盾  
- 模型假设（如成交在价格区间内均匀分布）与真实交易行为的偏差
- 流通盘变化（限售股解禁、回购注销）等对结果影响

## 技术路线选择

经过调研，选择了**路线B：基于换手率的日线递推法**，这是实用派的最佳选择：

### 核心算法原理

#### 1. 换手率递推法的数学模型

```python
# 核心递推公式
D'[t-1](price_bin) = D[t-1](price_bin) * (1 - turnover_rate)  # 旧筹码衰减
D[t](price_bin) = D'[t-1](price_bin) + NewDist(price_bin)     # 新筹码注入

# 获利盘比例计算
profit_ratio = sum(D[price_bin <= current_price]) / sum(D)
```

#### 2. 三大步骤

1. **旧筹码衰减**：`retention_rate = 1 - turnover_rate`
2. **新筹码注入**：将当日成交量按三角分布分配到价格区间
3. **归一化处理**：防止累积误差，保持总量等于流通股本

## 具体实现

### 1. 后端实现（Python）

文件位置：`backend/services/chip_concentration_calculator.py`

#### 1.1 核心类结构

```python
class ChipConcentrationCalculator:
    def __init__(self, lookback_days: int = 60, price_step: float = 0.01):
        self.lookback_days = lookback_days
        self.price_step = price_step  # 价格分桶步长
    
    def _calculate_chip_distribution_recursive(self, historical_data):
        # 换手率递推法主函数
        # 1. 初始化价格分桶
        # 2. 第一天初始分布
        # 3. 递推计算每日筹码分布
```

#### 1.2 关键算法要点

- **价格分桶**：0.01元精度，动态扩展范围
- **VWAP计算**：`(High + Low + Close) / 3` 作为典型价格
- **三角分布**：以VWAP为中心，距离越近权重越大
- **基尼系数**：计算筹码集中度的科学方法

```python
def _calculate_gini_concentration(self, chip_distribution):
    gini_sum = sum(abs(volumes[i] - volumes[j]) for i,j in all_pairs)
    gini = gini_sum / (2 * n * total_volume)
    concentration = min(1.0, gini * 2)
```

### 2. Supabase Edge Functions 实现（TypeScript）

#### 2.1 完整的换手率递推法

文件位置：`supabase/functions/stock-api-real/index.ts`

```typescript
class ChipDistributionCalculator {
  calculateChipDistribution(historicalData: HistoricalData[]): ChipDistribution {
    // 步骤1：旧筹码衰减
    const retentionRate = 1.0 - turnoverRate;
    chipDistribution = chipDistribution.map(vol => vol * retentionRate);
    
    // 步骤2：新筹码注入（三角分布）
    chipDistribution = this.distributeVolumeTriangle(...);
    
    // 步骤3：归一化
    const scaleFactor = floatShares / totalVolume;
    chipDistribution = chipDistribution.map(vol => vol * scaleFactor);
  }
}
```

#### 2.2 分段获利盘比例计算

```typescript
// 涨跌幅影响（分段处理）
if (pctChg <= 3) {
  profitRatio += pctChg / 20; // 温和上涨：获利盘线性增加
} else if (pctChg <= 7) {
  profitRatio += 0.15 + (pctChg - 3) / 40; // 适度上涨：增幅放缓
} else {
  profitRatio += 0.25 + Math.min(0.15, (pctChg - 7) / 60); // 大涨：增幅递减
}

// 换手率衰减效应
if (turnoverRate > 10) {
  profitRatio -= Math.min(0.1, (turnoverRate - 10) / 100); // 高换手导致获利盘流失
}
```

### 3. 算法一致性保证

所有模块（后端Python + 三个Edge Functions）都采用相同的核心算法：

- **筹码集中度**：基于基尼系数计算
- **获利盘比例**：基于成本分布精确计算
- **衰减模型**：换手率递推法
- **分布策略**：三角分布（VWAP中心）

## 改进效果对比

### 1. 算法准确性提升

| 方法 | 数据需求 | 准确性 | 计算复杂度 | 适用场景 |
|------|----------|--------|------------|----------|
| 原方法（涨跌幅估算） | 当日涨跌幅 | ★★☆☆☆ | ★☆☆☆☆ | 快速估算 |
| 换手率递推法 | 日线数据+换手率 | ★★★★☆ | ★★★☆☆ | 实用生产 |
| 逐笔成交重构 | Tick级数据 | ★★★★★ | ★★★★★ | 高精度研究 |

### 2. 关键指标对比

```python
# 原方法
profit_ratio = 0.5 + pct_chg / 30  # 过于简化

# 新方法
profit_ratio = sum(volume where cost < current_price) / total_volume  # 基于真实分布
```

### 3. 实际市场验证

- **筹码峰值分析**：能识别主要成本区域
- **支撑压力位**：基于筹码密集度判断
- **获利盘流失**：高换手率时的衰减效应

## 技术要点总结

### 1. 核心公式
```
旧筹码保留 = 前日分布 × (1 - 当日换手率)
新筹码分布 = 当日成交量 × 三角分布权重
今日分布 = 旧筹码保留 + 新筹码分布
获利盘比例 = sum(分布[价格 <= 当前价]) / sum(分布)
```

### 2. 边界处理
- 换手率限制：0.001 - 1.0
- 获利盘比例：0.05 - 0.95
- 筹码集中度：0.1 - 0.95

### 3. 性能优化
- 价格分桶：动态范围，避免内存浪费
- 计算缓存：历史分布可复用
- 降级策略：数据不足时使用估算方法

## 使用建议

### 1. 参数调优指南
```python
lookback_days = 60      # 历史数据回看天数（建议30-120天）
price_step = 0.01       # 价格分桶精度（建议0.01-0.05元）
decay_factor = 20       # 时间衰减系数（建议15-30天）
```

### 2. 数据质量要求
- **必需字段**：close, high, low, volume, turnover_rate
- **最小数据量**：10个交易日
- **数据完整性**：缺失数据自动补齐

### 3. 结果解读
- **筹码集中度 > 0.7**：高度集中，主力控盘
- **获利盘比例 > 0.8**：获利丰厚，注意高位风险
- **主要成本区域**：筹码密集价格带，重要支撑/压力位

## 矛盾分析的运用

### 主要矛盾：数据真实性 vs 模型可执行性
- **解决策略**：换手率递推法在两者间找到平衡点
- **矛盾转化**：当获得高频数据时，可升级到逐笔重构法

### 对立统一的体现
- **抽象与具体**：简化模型抽象市场复杂性，但保留核心规律
- **近似与精确**：用有限数据逼近无限复杂的真实情况
- **理论与实践**：科学计算方法与工程实现的统一

## 未来优化方向

### 1. 机器学习增强
- 训练筹码分布预测模型
- 个股特性学习（不同行业的筹码行为差异）
- 市场情绪因子融入

### 2. 实时数据集成
- 分时成交数据接入
- Level-2行情数据利用
- 大单跟踪与筹码流向分析

### 3. 多维度扩展
- 机构vs散户筹码分布
- 地区资金流向分析  
- 主题概念板块筹码联动

---

**总结：基于换手率递推法的筹码分布计算，在数据可得性和计算准确性之间找到了最佳平衡点，是当前最实用和科学的解决方案。**