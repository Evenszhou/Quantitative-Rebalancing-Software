// ============================================================================
// ResultDisplay - Backtest Results Dashboard
// Shows performance metrics, return curve, drawdown chart, and position table
// ============================================================================

import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Typography,
  Tabs,
  Tooltip,
  Empty,
  Spin,
  message,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DownloadOutlined,
  TrophyOutlined,
  WarningOutlined,
  FundOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import { ReturnCurve, DrawdownCurve } from '../Charts';
import { useAppStore } from '@/store/useAppStore';
import { downloadExport } from '@/services/api';
import type { TableProps } from 'antd';
import type { TradeLogEntry } from '@/types';

const { Title, Text } = Typography;

/**
 * Format number as percentage string
 */
const fmtPct = (v: number, decimals = 2): string =>
  `${(v * 100).toFixed(decimals)}%`;

/**
 * Format number as currency
 */
const fmtCurrency = (v: number): string =>
  `¥${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/**
 * Color coding for metrics: positive = green, negative = red
 */
const getMetricColor = (value: number, inverse = false): string => {
  if (inverse) {
    // For metrics like drawdown where lower is better
    return value > 0 ? '#ff4d4f' : value < 0 ? '#3f8600' : '#666';
  }
  return value > 0 ? '#3f8600' : value < 0 ? '#ff4d4f' : '#666';
};

/**
 * Main ResultDisplay component
 */
const ResultDisplay: React.FC = () => {
  const { backtestResult, isRunningBacktest } = useAppStore();
  const [isExporting, setIsExporting] = useState(false);

  /** Handle Excel export */
  const handleExport = async () => {
    if (!backtestResult) return;
    setIsExporting(true);
    try {
      await downloadExport(backtestResult.task_id);
      message.success('导出成功 / Export successful');
    } catch {
      // Error handled by API interceptor
    } finally {
      setIsExporting(false);
    }
  };

  // Loading state
  if (isRunningBacktest) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <Spin size="large" />
        <Title level={4} style={{ marginTop: 24 }}>
          回测运行中... / Running Backtest...
        </Title>
        <Text type="secondary">请耐心等待结果 / Please wait for results</Text>
      </div>
    );
  }

  // No result yet
  if (!backtestResult) {
    return (
      <Empty
        style={{ padding: '80px 0' }}
        description={
          <Space direction="vertical">
            <Text>暂无回测结果</Text>
            <Text type="secondary">
              请先上传数据，配置参数后运行回测 / Upload data, configure, and run
              backtest
            </Text>
          </Space>
        }
      />
    );
  }

  const { metrics, returns_series, position_series, trade_log } =
    backtestResult;

  return (
    <div className="result-display">
      {/* Performance Metrics Cards */}
      <Card
        className="result-card"
        title={
          <Space>
            <TrophyOutlined />
            <span>绩效指标 / Performance Metrics</span>
          </Space>
        }
        extra={
          <Tooltip title="导出 Excel / Export to Excel">
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              loading={isExporting}
              type="primary"
              ghost
            >
              导出 / Export
            </Button>
          </Tooltip>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="年化收益率 / Annual Return"
              value={metrics.annual_return}
              precision={2}
              formatter={(v) => fmtPct(v as number)}
              valueStyle={{
                color: getMetricColor(metrics.annual_return),
              }}
              prefix={
                metrics.annual_return >= 0 ? (
                  <ArrowUpOutlined />
                ) : (
                  <ArrowDownOutlined />
                )
              }
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="基准收益率 / Baseline Return"
              value={metrics.baseline_return}
              precision={2}
              formatter={(v) => fmtPct(v as number)}
              valueStyle={{
                color: getMetricColor(metrics.baseline_return),
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="超额收益 / Excess Return"
              value={metrics.excess_return}
              precision={2}
              formatter={(v) => fmtPct(v as number)}
              valueStyle={{
                color: getMetricColor(metrics.excess_return),
              }}
              prefix={
                metrics.excess_return >= 0 ? (
                  <ArrowUpOutlined />
                ) : (
                  <ArrowDownOutlined />
                )
              }
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="年化波动率 / Annual Volatility"
              value={metrics.annual_volatility}
              precision={2}
              formatter={(v) => fmtPct(v as number)}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="夏普比率 / Sharpe Ratio"
              value={metrics.sharpe_ratio}
              precision={3}
              valueStyle={{
                color:
                  metrics.sharpe_ratio >= 1
                    ? '#3f8600'
                    : metrics.sharpe_ratio >= 0
                      ? '#faad14'
                      : '#ff4d4f',
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="最大回撤 / Max Drawdown"
              value={metrics.max_drawdown}
              precision={2}
              formatter={(v) => fmtPct(v as number)}
              valueStyle={{
                color: getMetricColor(metrics.max_drawdown, true),
              }}
              prefix={<WarningOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="Calmar 比率"
              value={metrics.calmar_ratio}
              precision={3}
              valueStyle={{
                color: getMetricColor(metrics.calmar_ratio),
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="Sortino 比率"
              value={metrics.sortino_ratio}
              precision={3}
              valueStyle={{
                color: getMetricColor(metrics.sortino_ratio),
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="信息比率 / Info Ratio"
              value={metrics.information_ratio}
              precision={3}
              valueStyle={{
                color: getMetricColor(metrics.information_ratio),
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="胜率 / Win Rate"
              value={metrics.win_rate}
              precision={2}
              formatter={(v) => fmtPct(v as number)}
              valueStyle={{
                color: metrics.win_rate >= 0.5 ? '#3f8600' : '#ff4d4f',
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="总交易次数 / Total Trades"
              value={metrics.total_trades}
              suffix="次"
            />
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Statistic
              title="总交易成本 / Total Cost"
              value={metrics.total_transaction_cost}
              precision={2}
              formatter={(v) => fmtCurrency(v as number)}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<SwapOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* Charts */}
      <Tabs
        className="result-tabs"
        defaultActiveKey="returns"
        items={[
          {
            key: 'returns',
            label: (
              <Space>
                <FundOutlined />
                净值曲线 / NAV Curve
              </Space>
            ),
            children: (
              <Card className="result-card" bodyStyle={{ padding: 16 }}>
                <ReturnCurve data={returns_series} height={420} />
              </Card>
            ),
          },
          {
            key: 'drawdown',
            label: (
              <Space>
                <WarningOutlined />
                回撤曲线 / Drawdown
              </Space>
            ),
            children: (
              <Card className="result-card" bodyStyle={{ padding: 16 }}>
                <DrawdownCurve data={returns_series} height={320} />
              </Card>
            ),
          },
        ]}
      />

      {/* Position Series Table */}
      {position_series && Object.keys(position_series).length > 0 && (
        <Card
          className="result-card"
          title={
            <Space>
              <FundOutlined />
              <span>仓位变化 / Position Changes</span>
            </Space>
          }
        >
          <PositionTable positionSeries={position_series} />
        </Card>
      )}

      {/* Trade Log Table */}
      {trade_log && trade_log.length > 0 && (
        <Card
          className="result-card"
          title={
            <Space>
              <SwapOutlined />
              <span>交易记录 / Trade Log</span>
              <Tag color="blue">{trade_log.length}</Tag>
            </Space>
          }
        >
          <Table
            dataSource={trade_log}
            columns={tradeLogColumns}
            rowKey={(record, index) => `${record.date}-${index}`}
            size="small"
            scroll={{ x: 400 }}
            pagination={{ pageSize: 20, showSizeChanger: true }}
          />
        </Card>
      )}
    </div>
  );
};

/**
 * Position changes table - shows asset weights per rebalance date
 */
const PositionTable: React.FC<{
  positionSeries: Record<string, Record<string, number>>;
}> = ({ positionSeries }) => {
  const dates = Object.keys(positionSeries).sort();
  if (dates.length === 0) return null;

  // Get all asset names from the first entry
  const assets = Object.keys(positionSeries[dates[0]] || {});

  const columns: NonNullable<TableProps['columns']> = [
    {
      title: '日期 / Date',
      dataIndex: 'date',
      key: 'date',
      fixed: 'left',
      width: 120,
    },
    ...assets.map((asset) => ({
      title: asset,
      dataIndex: asset,
      key: asset,
      width: 100,
      render: (value: number) => (
        <Tag color={value > 0.3 ? 'green' : value > 0.1 ? 'blue' : 'default'}>
          {(value * 100).toFixed(2)}%
        </Tag>
      ),
    })),
  ];

  const dataSource = dates.map((date) => ({
    date,
    key: date,
    ...positionSeries[date],
  }));

  return (
    <Table
      dataSource={dataSource}
      columns={columns}
      size="small"
      scroll={{ x: 120 + assets.length * 100 }}
      pagination={{ pageSize: 20, showSizeChanger: true }}
    />
  );
};

/**
 * Trade log column definitions
 */
const tradeLogColumns: NonNullable<TableProps<TradeLogEntry>['columns']> = [
  {
    title: '日期 / Date',
    dataIndex: 'date',
    key: 'date',
    width: 120,
  },
  {
    title: '类型 / Type',
    dataIndex: 'type',
    key: 'type',
    width: 120,
    render: (type: string) => (
      <Tag color={type === 'rebalance' ? 'blue' : 'orange'}>{type}</Tag>
    ),
  },
  {
    title: '交易成本 / Cost',
    dataIndex: 'total_cost',
    key: 'total_cost',
    width: 150,
    render: (cost: number) => (
      <Text type="danger">{fmtCurrency(cost)}</Text>
    ),
  },
];

export default ResultDisplay;
