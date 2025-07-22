// 工具函数

import dayjs from 'dayjs';
import { message } from 'antd';

/**
 * 格式化数字为百分比
 */
export const formatPercent = (value: number, decimals: number = 2): string => {
  // 安全检查，避免NaN或undefined
  const safeValue = Number(value);
  if (isNaN(safeValue)) {
    return '0.00%';
  }
  return `${(safeValue * 100).toFixed(decimals)}%`;
};

/**
 * 格式化数字为货币
 */
export const formatCurrency = (value: number, decimals: number = 2): string => {
  const safeValue = Number(value);
  if (isNaN(safeValue)) {
    return '¥0.00';
  }
  return `¥${safeValue.toLocaleString('zh-CN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};

/**
 * 格式化大数字（万、亿）
 */
export const formatLargeNumber = (value: number): string => {
  const safeValue = Number(value);
  if (isNaN(safeValue)) {
    return '0.00';
  }
  if (safeValue >= 100000000) {
    return `${(safeValue / 100000000).toFixed(2)}亿`;
  } else if (safeValue >= 10000) {
    return `${(safeValue / 10000).toFixed(2)}万`;
  }
  return safeValue.toFixed(2);
};

/**
 * 格式化日期
 */
export const formatDate = (date: string | Date, format: string = 'YYYY-MM-DD'): string => {
  return dayjs(date).format(format);
};

/**
 * 格式化时间
 */
export const formatDateTime = (date: string | Date): string => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

/**
 * 获取涨跌颜色
 */
export const getChangeColor = (value: number): string => {
  if (value > 0) return '#f5222d'; // 红色
  if (value < 0) return '#52c41a'; // 绿色
  return '#666666'; // 灰色
};

/**
 * 获取涨跌文本
 */
export const getChangeText = (value: number): string => {
  const safeValue = Number(value);
  if (isNaN(safeValue)) {
    return '0.00%';
  }
  const prefix = safeValue > 0 ? '+' : '';
  return `${prefix}${safeValue.toFixed(2)}%`;
};

/**
 * 下载文件
 */
export const downloadFile = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * 复制到剪贴板
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
    return true;
  } catch (error) {
    message.error('复制失败');
    return false;
  }
};

/**
 * 防抖函数
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * 节流函数
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * 获取随机颜色
 */
export const getRandomColor = (): string => {
  const colors = [
    '#1890ff', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1',
    '#13c2c2', '#faad14', '#f5222d', '#a0d911', '#1890ff'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

/**
 * 验证股票代码格式
 */
export const validateStockCode = (code: string): boolean => {
  // A股股票代码格式：6位数字.交易所代码
  const pattern = /^\d{6}\.(SH|SZ)$/;
  return pattern.test(code);
};

/**
 * 计算收益率颜色
 */
export const getReturnColor = (value: number): string => {
  if (value > 0.1) return '#ff4d4f';
  if (value > 0.05) return '#fa8c16';
  if (value > 0) return '#52c41a';
  if (value > -0.05) return '#1890ff';
  if (value > -0.1) return '#722ed1';
  return '#8c8c8c';
};

/**
 * 获取评分等级
 */
export const getScoreLevel = (score: number): {
  level: string;
  color: string;
  description: string;
} => {
  if (score >= 80) {
    return { level: 'A', color: '#f5222d', description: '强烈推荐' };
  } else if (score >= 70) {
    return { level: 'B', color: '#fa8c16', description: '推荐' };
  } else if (score >= 60) {
    return { level: 'C', color: '#faad14', description: '一般' };
  } else if (score >= 50) {
    return { level: 'D', color: '#1890ff', description: '观望' };
  } else {
    return { level: 'E', color: '#8c8c8c', description: '不推荐' };
  }
};

/**
 * 错误处理函数
 */
export const handleError = (error: any, defaultMessage: string = '操作失败'): void => {
  console.error('Error:', error);
  const errorMessage = error?.response?.data?.detail || error?.message || defaultMessage;
  message.error(errorMessage);
};

/**
 * 生成UUID
 */
export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};
