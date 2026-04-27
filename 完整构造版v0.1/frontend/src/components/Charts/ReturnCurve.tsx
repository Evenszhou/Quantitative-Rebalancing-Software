// ============================================================================
// ReturnCurve - Portfolio vs Baseline Return Curve Chart (ECharts)
// ============================================================================

import React from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { ReturnSeriesPoint } from '@/types';

interface ReturnCurveProps {
  /** Time series data: { [date]: { portfolio: number, baseline: number } } */
  data: Record<string, ReturnSeriesPoint>;
  /** Chart height in pixels */
  height?: number;
}

/**
 * Portfolio return curve vs baseline comparison
 * Normalizes both series to start at 1.0
 */
const ReturnCurve: React.FC<ReturnCurveProps> = ({ data, height = 400 }) => {
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

  // Sort dates and build series
  const dates = Object.keys(data).sort();
  const portfolioValues: number[] = [];
  const baselineValues: number[] = [];

  // Normalize to start at 1.0
  const firstPortfolio = data[dates[0]]?.portfolio || 1;
  const firstBaseline = data[dates[0]]?.baseline || 1;

  dates.forEach((date) => {
    const point = data[date];
    portfolioValues.push(
      point ? point.portfolio / firstPortfolio : 1
    );
    baselineValues.push(
      point ? point.baseline / firstBaseline : 1
    );
  });

  const option: EChartsOption = {
    title: {
      text: '净值曲线 / NAV Curve',
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
          result += `${item.seriesName}: <b>${item.value.toFixed(4)}</b><br/>`;
        });
        return result;
      },
    },
    legend: {
      data: ['组合 / Portfolio', '基准 / Baseline'],
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
      name: '净值 / NAV',
      axisLabel: {
        formatter: (value: number) => value.toFixed(2),
      },
    },
    series: [
      {
        name: '组合 / Portfolio',
        type: 'line',
        data: portfolioValues,
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: '#1677ff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(22,119,255,0.3)' },
              { offset: 1, color: 'rgba(22,119,255,0.02)' },
            ],
          },
        },
        showSymbol: false,
      },
      {
        name: '基准 / Baseline',
        type: 'line',
        data: baselineValues,
        smooth: true,
        lineStyle: { width: 2, type: 'dashed' },
        itemStyle: { color: '#faad14' },
        showSymbol: false,
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} notMerge />;
};

export default ReturnCurve;
