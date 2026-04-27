// ============================================================================
// DrawdownCurve - Portfolio Drawdown Curve Chart (ECharts)
// ============================================================================

import React from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { ReturnSeriesPoint } from '@/types';

interface DrawdownCurveProps {
  /** Time series data: { [date]: { portfolio: number, baseline: number } } */
  data: Record<string, ReturnSeriesPoint>;
  /** Chart height in pixels */
  height?: number;
}

/**
 * Calculates and displays the maximum drawdown curve over time.
 * Drawdown is calculated as the percentage decline from the running maximum.
 */
const DrawdownCurve: React.FC<DrawdownCurveProps> = ({
  data,
  height = 300,
}) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
        }}
      >
        暂无数据 / No data available
      </div>
    );
  }

  // Sort dates
  const dates = Object.keys(data).sort();

  // Calculate drawdown series
  const portfolioDrawdown: number[] = [];
  const baselineDrawdown: number[] = [];
  let maxPortfolio = -Infinity;
  let maxBaseline = -Infinity;

  dates.forEach((date) => {
    const point = data[date];
    if (!point) return;

    // Portfolio drawdown
    maxPortfolio = Math.max(maxPortfolio, point.portfolio);
    const ddPortfolio =
      maxPortfolio > 0
        ? (point.portfolio - maxPortfolio) / maxPortfolio
        : 0;
    portfolioDrawdown.push(parseFloat((ddPortfolio * 100).toFixed(4)));

    // Baseline drawdown
    maxBaseline = Math.max(maxBaseline, point.baseline);
    const ddBaseline =
      maxBaseline > 0
        ? (point.baseline - maxBaseline) / maxBaseline
        : 0;
    baselineDrawdown.push(parseFloat((ddBaseline * 100).toFixed(4)));
  });

  const option: EChartsOption = {
    title: {
      text: '回撤曲线 / Drawdown Curve',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const p = params as Array<{
          axisValue: string;
          seriesName: string;
          value: number;
        }>;
        if (!Array.isArray(p)) return '';
        let result = `<b>${p[0].axisValue}</b><br/>`;
        p.forEach((item) => {
          result += `${item.seriesName}: <b>${item.value.toFixed(2)}%</b><br/>`;
        });
        return result;
      },
    },
    legend: {
      data: ['组合回撤 / Portfolio DD', '基准回撤 / Baseline DD'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '12%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 30,
        formatter: (value: string) => value.substring(0, 10),
      },
    },
    yAxis: {
      type: 'value',
      name: '回撤% / DD%',
      axisLabel: {
        formatter: (value: number) => `${value.toFixed(1)}%`,
      },
    },
    series: [
      {
        name: '组合回撤 / Portfolio DD',
        type: 'line',
        data: portfolioDrawdown,
        smooth: true,
        lineStyle: { width: 1.5 },
        itemStyle: { color: '#ff4d4f' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255,77,79,0.02)' },
              { offset: 1, color: 'rgba(255,77,79,0.3)' },
            ],
          },
        },
        showSymbol: false,
      },
      {
        name: '基准回撤 / Baseline DD',
        type: 'line',
        data: baselineDrawdown,
        smooth: true,
        lineStyle: { width: 1.5, type: 'dashed' },
        itemStyle: { color: '#faad14' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(250,173,20,0.02)' },
              { offset: 1, color: 'rgba(250,173,20,0.15)' },
            ],
          },
        },
        showSymbol: false,
      },
    ],
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100 },
    ],
  };

  return <ReactECharts option={option} style={{ height }} notMerge />;
};

export default DrawdownCurve;
