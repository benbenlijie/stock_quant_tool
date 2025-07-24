# 获利盘比例计算优化文档

## 背景

原有的获利盘比例计算方法过于简化，仅基于当日涨跌幅进行估算，缺乏准确性。本次优化旨在提供更准确、更符合市场规律的获利盘比例计算方法。

## 改进方案

### 1. Tushare API 调研结果

经过调研，Tushare API 暂时不提供筹码分布或获利盘比例的直接接口，因此需要通过算法优化来提升计算准确性。

### 2. 后端优化（Python）

#### 2.1 增强的筹码集中度计算器

文件位置：`backend/services/chip_concentration_calculator.py`

主要改进：
- **筹码分布建模**：基于历史价格和成交量数据构建筹码成本分布
- **时间权重衰减**：近期交易数据权重更高，使用指数衰减模型
- **换手率调整**：高换手率表示筹码变动更大
- **基尼系数计算**：使用基尼系数计算筹码集中度
- **精确获利盘比例**：根据成本分布计算当前价格下的获利筹码比例

#### 2.2 算法流程

```python
def calculate_chip_concentration(self, current_price: float, historical_data: pd.DataFrame):
    # 1. 构建筹码成本分布
    cost_distribution = self._calculate_cost_distribution(historical_data)
    
    # 2. 计算筹码集中度（基尼系数）
    concentration = self._calculate_concentration_from_distribution(cost_distribution)
    
    # 3. 计算获利盘比例
    profit_ratio = self._calculate_profit_ratio(current_price, cost_distribution)
    
    # 4. 计算筹码稳定性
    stability = self._calculate_chip_stability(historical_data)
    
    return {
        'chip_concentration': concentration,
        'profit_ratio': profit_ratio,
        'chip_stability': stability
    }
```

#### 2.3 筹码分布计算要点

- **时间衰减**：使用 `exp(-days_ago / 20)` 进行时间权重衰减
- **换手率权重**：`min(2.0, 1 + turnover_rate / 100)`
- **价格区间分布**：在日内高低价区间内均匀分布筹码
- **边界处理**：获利盘比例限制在 0.05-0.95 之间

### 3. Supabase Edge Functions 优化（TypeScript）

#### 3.1 stock-api-real 函数优化

文件位置：`supabase/functions/stock-api-real/index.ts`

主要改进：
- **增强计算函数**：`calculateEnhancedChipMetrics()` 支持历史数据输入
- **筹码分布算法**：实现与后端一致的筹码分布计算逻辑
- **多因子获利盘模型**：基于涨跌幅、换手率、量比的综合计算

#### 3.2 多因子获利盘比例计算

```typescript
// 涨跌幅影响（分段处理）
if (pctChg <= 3) {
  profitRatio += pctChg / 20; // 温和上涨
} else if (pctChg <= 7) {
  profitRatio += 0.15 + (pctChg - 3) / 40; // 适度上涨
} else {
  profitRatio += 0.25 + Math.min(0.15, (pctChg - 7) / 60); // 大涨但增幅递减
}

// 换手率影响
if (turnoverRate > 10) {
  profitRatio -= Math.min(0.1, (turnoverRate - 10) / 100);
}

// 量比影响
if (volumeRatio > 1.5 && pctChg > 2) {
  profitRatio += Math.min(0.05, (volumeRatio - 1.5) / 20);
}
```

#### 3.3 其他函数同步更新

- `backtest-engine/index.ts`：更新模拟数据生成逻辑
- `stock-api/index.ts`：同步计算方法，确保一致性

## 改进效果

### 1. 准确性提升
- 基于历史数据的筹码分布建模，比简单涨跌幅估算更准确
- 考虑时间衰减和换手率影响，更符合市场实际情况

### 2. 算法健壮性
- 多层级后备方案：增强算法 → 改进估算 → 简单计算
- 边界处理和异常容错机制

### 3. 一致性保证
- 后端 Python 和前端 TypeScript 使用相同的计算逻辑
- 所有 Edge Function 同步更新

## 技术要点

### 1. 基尼系数计算筹码集中度
```python
gini = sum(|volumes[i] - volumes[j]|) / (2 * n * total_volume)
concentration = min(1.0, gini * 2)
```

### 2. 获利盘比例精确计算
```python
profit_ratio = sum(volume where price < current_price) / total_volume
```

### 3. 时间权重衰减模型
```python
time_weight = exp(-days_ago / 20)  # 20天衰减系数
```

## 使用建议

1. **优先使用增强算法**：当有足够历史数据（≥10天）时，使用基于筹码分布的计算方法
2. **后备方案**：数据不足时自动切换到改进的估算方法
3. **参数调优**：可根据实际效果调整时间衰减系数、权重因子等参数
4. **监控验证**：建议与实际市场表现进行对比验证，持续优化算法

## 未来优化方向

1. **机器学习增强**：收集历史数据训练获利盘比例预测模型
2. **实时数据接入**：接入更多实时数据源提升计算精度
3. **个股特性**：考虑不同行业、板块的筹码特性差异
4. **市场情绪**：结合市场整体情绪指标进行调整