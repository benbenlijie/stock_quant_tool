// A股量化选股系统API服务
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// 增强的筹码集中度计算函数（用于模拟数据生成）
function generateRealisticChipMetrics(pctChg: number, turnoverRate: number, volumeRatio: number): [number, number] {
  // 基于市场规律生成更真实的筹码集中度和获利盘比例
  
  // 筹码集中度计算
  let baseConcentration = 0.5;
  
  // 换手率因子：适度换手率最佳
  const optimalTurnover = 8.0;
  let turnoverFactor = 1.0 - Math.abs(turnoverRate - optimalTurnover) / 20.0;
  turnoverFactor = Math.max(0.3, Math.min(1.2, turnoverFactor));
  
  // 量比因子：适度放量表示有资金介入
  const volumeFactor = Math.min(1.3, Math.max(0.7, 0.8 + volumeRatio / 10));
  
  // 涨幅因子：适度上涨配合集中度
  let priceFactor = 1.0;
  if (pctChg >= 2 && pctChg <= 8) {
    priceFactor = 1.1;
  } else if (pctChg > 9) {
    priceFactor = 1.2;
  } else if (pctChg < -3) {
    priceFactor = 0.9;
  }
  
  // 综合计算集中度
  let concentration = baseConcentration * turnoverFactor * volumeFactor * priceFactor;
  concentration = Math.max(0.2, Math.min(0.95, concentration));
  
  // 获利盘比例计算 - 基于多因子模型
  let profitRatio = 0.5; // 基础获利盘比例
  
  // 涨跌幅影响
  if (pctChg > 0) {
    // 上涨时获利盘增加，但需要考虑涨幅大小
    if (pctChg <= 3) {
      profitRatio += pctChg / 20; // 温和上涨
    } else if (pctChg <= 7) {
      profitRatio += 0.15 + (pctChg - 3) / 40; // 适度上涨
    } else {
      profitRatio += 0.25 + Math.min(0.15, (pctChg - 7) / 60); // 大涨但增幅递减
    }
  } else {
    // 下跌时获利盘减少
    profitRatio += Math.max(-0.3, pctChg / 15);
  }
  
  // 换手率影响 - 高换手可能意味着获利盘在减少
  if (turnoverRate > 10) {
    profitRatio -= Math.min(0.1, (turnoverRate - 10) / 100);
  }
  
  // 量比影响 - 放量上涨增加获利盘可信度
  if (volumeRatio > 1.5 && pctChg > 2) {
    profitRatio += Math.min(0.05, (volumeRatio - 1.5) / 20);
  }
  
  profitRatio = Math.max(0.1, Math.min(0.9, profitRatio));
  
  return [concentration, profitRatio];
}

Deno.serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'false'
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    let path = url.pathname;
    
    // 移除 Supabase 函数前缀
    if (path.startsWith('/stock-api')) {
      path = path.replace('/stock-api', '');
    }
    if (path === '') {
      path = '/';
    }
    
    const method = req.method;

    console.log(`API请求: ${method} ${path} (原始: ${url.pathname})`);

    // 模拟数据生成器
    const generateMockStocks = (count = 20) => {
      const stockNames = [
        "东方通信", "领益智造", "中科创达", "卓胜微", "沪硅产业",
        "金龙鱼", "宁德时代", "比亚迪", "隆基绿能", "通威股份",
        "药明康德", "迈瑞医疗", "恒瑞医药", "片仔癀", "云南白药",
        "贵州茅台", "五粮液", "泸州老窖", "山西汾酒", "今世缘"
      ];
      
      const themes = ["5G通信", "新能源", "半导体", "医药生物", "白酒", "光伏", "汽车", "AI概念"];
      
      const stocks = [];
      for (let i = 0; i < count; i++) {
        const tsCode = i % 2 === 0 ? `0${String(i+1).padStart(5, '0')}.SZ` : `6${String(i+1).padStart(5, '0')}.SH`;
        const [concentration, profitRatio] = generateRealisticChipMetrics(
          Math.round((Math.random() * 10 - 5) * 100) / 100, // pct_chg
          Math.round((Math.random() * 25 + 10) * 100) / 100, // turnover_rate
          Math.round((Math.random() * 6 + 2) * 100) / 100 // volume_ratio
        );
        stocks.push({
          ts_code: tsCode,
          name: stockNames[i % stockNames.length],
          close: Math.round((Math.random() * 90 + 10) * 100) / 100,
          pct_chg: Math.round((Math.random() * 5.01 + 5) * 100) / 100,
          turnover_rate: Math.round((Math.random() * 25 + 10) * 100) / 100,
          volume_ratio: Math.round((Math.random() * 6 + 2) * 100) / 100,
          total_score: Math.round((Math.random() * 35 + 60) * 10) / 10,
          rank_position: i + 1,
          reason: "技术突破+量价齐升+题材热度",
          market_cap: Math.round((Math.random() * 80 + 20) * 100) / 100,
          amount: Math.floor(Math.random() * 450000 + 50000),
          theme: themes[i % themes.length],
          chip_concentration: concentration,
          profit_ratio: profitRatio,
          dragon_tiger_net_amount: Math.floor(Math.random() * 150000000 - 50000000)
        });
      }
      return stocks;
    };

    const generateMarketSentiment = () => {
      return {
        limit_up_count: Math.floor(Math.random() * 60 + 20),
        limit_times_distribution: {
          "2": Math.floor(Math.random() * 10 + 5),
          "3": Math.floor(Math.random() * 7 + 3),
          "4": Math.floor(Math.random() * 4 + 1),
          "5": Math.floor(Math.random() * 3)
        },
        avg_open_times: Math.round((Math.random() * 2.3 + 1.2) * 100) / 100,
        total_limit_stocks: Math.floor(Math.random() * 20 + 10),
        zhaban_rate: Math.round((Math.random() * 0.5 + 0.2) * 1000) / 1000
      };
    };

    const getCurrentTimestamp = () => new Date().toISOString();

    // 路由处理
    if (path === '/' && method === 'GET') {
      return new Response(JSON.stringify({
        message: "A股连续涨停板量化选股系统API",
        status: "running",
        version: "1.0.0",
        timestamp: getCurrentTimestamp()
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Dashboard API
    if (path === '/dashboard' && method === 'GET') {
      const candidates = generateMockStocks(20);
      
      const data = {
        code: 200,
        message: "获取仪表盘数据成功",
        data: {
          market_sentiment: generateMarketSentiment(),
          today_candidates: candidates,
          strategy_stats: {
            total_analyzed: Math.floor(Math.random() * 2000 + 3000),
            candidate_count: candidates.length,
            avg_score: Math.round((Math.random() * 15 + 70) * 10) / 10
          },
          recent_performance: {
            last_update: getCurrentTimestamp(),
            data_status: "success"
          },
          update_time: getCurrentTimestamp()
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 候选股票API
    if (path === '/stocks/candidates' && method === 'GET') {
      const searchParams = new URLSearchParams(url.search);
      const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 50);
      const candidates = generateMockStocks(limit);
      
      const data = {
        code: 200,
        message: "获取候选股票成功",
        data: {
          trade_date: new Date().toISOString().split('T')[0],
          candidates: candidates,
          total_count: candidates.length
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 策略重新计算API
    if (path === '/strategy/recompute' && method === 'POST') {
      const data = {
        code: 200,
        message: "策略重新计算完成",
        data: {
          status: "completed",
          updated_count: Math.floor(Math.random() * 10 + 15),
          execution_time: Math.round((Math.random() * 6 + 2) * 100) / 100
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 设置API
    if (path === '/settings' && method === 'GET') {
      const data = {
        code: 200,
        message: "获取设置成功",
        data: {
          settings: {
            max_market_cap: "50",
            min_turnover_rate: "10",
            min_volume_ratio: "2",
            min_daily_gain: "9",
            max_stock_price: "30",
            chip_concentration_threshold: "0.65",
            profit_ratio_threshold: "0.5",
            volume_price_weight: "30",
            chip_weight: "25",
            dragon_tiger_weight: "20",
            theme_weight: "15",
            money_flow_weight: "10"
          },
          count: 12
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 设置更新API
    if (path === '/settings' && method === 'PUT') {
      const requestData = await req.json();
      
      const data = {
        code: 200,
        message: "设置更新成功",
        data: {
          setting_key: requestData.setting_key,
          setting_value: requestData.setting_value,
          updated_at: getCurrentTimestamp()
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 回测结果API
    if (path === '/backtest' && method === 'GET') {
      const results = [];
      for (let i = 0; i < 5; i++) {
        results.push({
          backtest_id: `bt_${Math.floor(Math.random() * 900000 + 100000)}`,
          start_date: "2024-01-01",
          end_date: "2024-12-31",
          status: "completed",
          total_return: Math.round((Math.random() * 0.7 + 0.1) * 10000) / 10000,
          annual_return: Math.round((Math.random() * 0.75 + 0.15) * 10000) / 10000,
          max_drawdown: Math.round((Math.random() * 0.2 + 0.05) * 10000) / 10000,
          sharpe_ratio: Math.round((Math.random() * 1.7 + 0.8) * 100) / 100,
          win_rate: Math.round((Math.random() * 0.25 + 0.4) * 1000) / 1000,
          total_trades: Math.floor(Math.random() * 150 + 50),
          created_at: getCurrentTimestamp()
        });
      }
      
      const data = {
        code: 200,
        message: "获取回测结果成功",
        data: {
          results: results,
          total_count: results.length
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 运行回测API
    if (path === '/backtest/run' && method === 'POST') {
      const requestData = await req.json();
      
      const result = {
        backtest_id: `bt_${Math.floor(Math.random() * 900000 + 100000)}`,
        start_date: requestData.start_date,
        end_date: requestData.end_date,
        status: "completed",
        total_return: Math.round((Math.random() * 0.4 + 0.2) * 10000) / 10000,
        annual_return: Math.round((Math.random() * 0.45 + 0.25) * 10000) / 10000,
        max_drawdown: Math.round((Math.random() * 0.12 + 0.08) * 10000) / 10000,
        sharpe_ratio: Math.round((Math.random() * 1.6 + 1.2) * 100) / 100,
        win_rate: Math.round((Math.random() * 0.2 + 0.45) * 1000) / 1000,
        total_trades: Math.floor(Math.random() * 70 + 80),
        created_at: getCurrentTimestamp()
      };
      
      const data = {
        code: 200,
        message: "回测运行成功",
        data: result,
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 导出数据API
    if (path === '/export' && method === 'POST') {
      const data = {
        code: 200,
        message: "数据导出功能暂未实现（演示版）",
        data: {
          export_url: "#",
          note: "演示版本不支持真实数据导出"
        },
        timestamp: getCurrentTimestamp()
      };
      
      return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // 404处理
    return new Response(JSON.stringify({
      code: 404,
      message: `API接口未找到: ${path}`,
      data: null,
      timestamp: getCurrentTimestamp(),
      debug: {
        original_path: url.pathname,
        processed_path: path,
        method: method
      }
    }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('API错误:', error);
    
    const errorResponse = {
      code: 500,
      message: "服务器内部错误",
      data: null,
      timestamp: new Date().toISOString(),
      error: error.message
    };

    return new Response(JSON.stringify(errorResponse), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
