// ============================================================================
// ConfigPanel - Configuration Panel Component
// Supports three modes: weighting | costs | backtest
// ============================================================================

import React from 'react';
import {
  Card,
  Form,
  Select,
  InputNumber,
  Slider,
  Switch,
  Collapse,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Table,
  Tag,
  Tooltip,
  Alert,
  Empty,
  Button,
} from 'antd';
import {
  SettingOutlined,
  PercentageOutlined,
  DollarOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import {
  WeightingMethod,
  RebalanceFreq,
  DEFAULT_TRANSACTION_COST,
} from '@/types';
import type { TransactionCost } from '@/types';

const { Panel } = Collapse;
const { Text } = Typography;

const WEIGHTING_METHOD_OPTIONS = [
  {
    value: WeightingMethod.EQUAL,
    label: '等权重 / Equal Weight',
    desc: 'Each asset gets equal allocation',
  },
  {
    value: WeightingMethod.RISK_PARITY,
    label: '风险平价 / Risk Parity',
    desc: 'Allocate based on risk contribution',
  },
  {
    value: WeightingMethod.MIN_VARIANCE,
    label: '最小方差 / Minimum Variance',
    desc: 'Minimize portfolio volatility',
  },
  {
    value: WeightingMethod.MAX_SHARPE,
    label: '最大夏普 / Maximum Sharpe',
    desc: 'Maximize risk-adjusted return',
  },
];

const REBALANCE_FREQ_OPTIONS = [
  { value: RebalanceFreq.MONTHLY, label: '每月 / Monthly' },
  { value: RebalanceFreq.QUARTERLY, label: '每季度 / Quarterly' },
  { value: RebalanceFreq.YEARLY, label: '每年 / Yearly' },
  { value: RebalanceFreq.NONE, label: '不复权 / No Rebalance' },
];

interface ConfigPanelProps {
  /** Panel type: controls which configuration sections are shown */
  type: 'weighting' | 'costs' | 'backtest';
}

/** Weighting configuration panel section */
const WeightingSection: React.FC = () => {
  const { backtestConfig, updateWeightingConfig } = useAppStore();
  const { weighting_config } = backtestConfig;

  return (
    <Form layout="vertical" size="small">
      <Form.Item label="权重方法 / Weighting Method">
        <Select
          value={weighting_config.method}
          onChange={(method: WeightingMethod) =>
            updateWeightingConfig({ method })
          }
          options={WEIGHTING_METHOD_OPTIONS.map((opt) => ({
            value: opt.value,
            label: (
              <div>
                <Text strong>{opt.label}</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {opt.desc}
                </Text>
              </div>
            ),
          }))}
        />
      </Form.Item>

      <Form.Item label="预热期 / Warmup Period">
        <Row gutter={16}>
          <Col span={18}>
            <Slider
              min={30}
              max={2000}
              value={weighting_config.warmup_period}
              onChange={(v) => updateWeightingConfig({ warmup_period: v })}
              marks={{
                30: '30',
                252: '1Y',
                504: '2Y',
                1260: '5Y',
                2000: '2000',
              }}
            />
          </Col>
          <Col span={6}>
            <InputNumber
              min={30}
              max={2000}
              value={weighting_config.warmup_period}
              onChange={(v) =>
                updateWeightingConfig({ warmup_period: v ?? 252 })
              }
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
      </Form.Item>

      {/* Max Sharpe specific options */}
      {weighting_config.method === WeightingMethod.MAX_SHARPE && (
        <>
          <Form.Item label="无风险利率 / Risk-Free Rate">
            <Row gutter={16}>
              <Col span={18}>
                <Slider
                  min={0}
                  max={0.1}
                  step={0.001}
                  value={weighting_config.risk_free_rate}
                  onChange={(v) => updateWeightingConfig({ risk_free_rate: v })}
                  tooltip={{
                    formatter: (v) => `${((v ?? 0) * 100).toFixed(1)}%`,
                  }}
                />
              </Col>
              <Col span={6}>
                <InputNumber
                  min={0}
                  max={0.1}
                  step={0.001}
                  value={weighting_config.risk_free_rate}
                  onChange={(v) =>
                    updateWeightingConfig({ risk_free_rate: v ?? 0.02 })
                  }
                  formatter={(v) => `${((v ?? 0) * 100).toFixed(1)}%`}
                  parser={(v) =>
                    parseFloat(v?.replace('%', '') ?? '0') / 100
                  }
                  style={{ width: '100%' }}
                />
              </Col>
            </Row>
          </Form.Item>

          <Form.Item label="允许做空 / Allow Short Selling">
            <Switch
              checked={weighting_config.allow_short}
              onChange={(checked) =>
                updateWeightingConfig({ allow_short: checked })
              }
            />
          </Form.Item>
        </>
      )}
    </Form>
  );
};

/** Transaction costs configuration panel section */
const CostsSection: React.FC = () => {
  const {
    uploadedFiles,
    backtestConfig,
    updateTransactionCosts,
    setDefaultTransactionCosts,
  } = useAppStore();

  const assetNames = uploadedFiles.map((f) => f.asset_name);

  const handleCostChange = (
    asset: string,
    field: keyof TransactionCost,
    value: number
  ) => {
    const currentCost =
      backtestConfig.transaction_costs[asset] || DEFAULT_TRANSACTION_COST;
    updateTransactionCosts(asset, {
      ...currentCost,
      [field]: value,
    });
  };

  const handleApplyToAll = () => {
    setDefaultTransactionCosts(DEFAULT_TRANSACTION_COST);
  };

  const transactionCostColumns = [
    {
      title: '资产 / Asset',
      dataIndex: 'asset',
      key: 'asset',
      render: (asset: string) => <Text strong>{asset}</Text>,
    },
    {
      title: (
        <Tooltip title="买入手续费率 / Buy commission rate">
          <span>买入% / Buy%</span>
        </Tooltip>
      ),
      dataIndex: 'buy_cost_pct',
      key: 'buy_cost_pct',
      render: (_: number, record: { asset: string }) => (
        <InputNumber
          size="small"
          min={0}
          max={0.1}
          step={0.0001}
          value={
            backtestConfig.transaction_costs[record.asset]?.buy_cost_pct ??
            DEFAULT_TRANSACTION_COST.buy_cost_pct
          }
          onChange={(v) =>
            handleCostChange(record.asset, 'buy_cost_pct', v ?? 0)
          }
          formatter={(v) => `${((v ?? 0) * 100).toFixed(2)}%`}
          parser={(v) => parseFloat(v?.replace('%', '') ?? '0') / 100}
          style={{ width: 90 }}
        />
      ),
    },
    {
      title: (
        <Tooltip title="卖出手续费率 / Sell commission rate">
          <span>卖出% / Sell%</span>
        </Tooltip>
      ),
      dataIndex: 'sell_cost_pct',
      key: 'sell_cost_pct',
      render: (_: number, record: { asset: string }) => (
        <InputNumber
          size="small"
          min={0}
          max={0.1}
          step={0.0001}
          value={
            backtestConfig.transaction_costs[record.asset]?.sell_cost_pct ??
            DEFAULT_TRANSACTION_COST.sell_cost_pct
          }
          onChange={(v) =>
            handleCostChange(record.asset, 'sell_cost_pct', v ?? 0)
          }
          formatter={(v) => `${((v ?? 0) * 100).toFixed(2)}%`}
          parser={(v) => parseFloat(v?.replace('%', '') ?? '0') / 100}
          style={{ width: 90 }}
        />
      ),
    },
    {
      title: (
        <Tooltip title="固定买入费用 / Fixed buy fee">
          <span>买入固定 / Buy Fixed</span>
        </Tooltip>
      ),
      dataIndex: 'buy_cost_fixed',
      key: 'buy_cost_fixed',
      render: (_: number, record: { asset: string }) => (
        <InputNumber
          size="small"
          min={0}
          max={100}
          step={0.5}
          value={
            backtestConfig.transaction_costs[record.asset]?.buy_cost_fixed ??
            DEFAULT_TRANSACTION_COST.buy_cost_fixed
          }
          onChange={(v) =>
            handleCostChange(record.asset, 'buy_cost_fixed', v ?? 0)
          }
          formatter={(v) => `¥${(v ?? 0).toFixed(2)}`}
          parser={(v) => parseFloat(v?.replace('¥', '') ?? '0')}
          style={{ width: 90 }}
        />
      ),
    },
    {
      title: (
        <Tooltip title="滑点率 / Slippage rate">
          <span>滑点% / Slip%</span>
        </Tooltip>
      ),
      dataIndex: 'slippage_pct',
      key: 'slippage_pct',
      render: (_: number, record: { asset: string }) => (
        <InputNumber
          size="small"
          min={0}
          max={0.05}
          step={0.0001}
          value={
            backtestConfig.transaction_costs[record.asset]?.slippage_pct ??
            DEFAULT_TRANSACTION_COST.slippage_pct
          }
          onChange={(v) =>
            handleCostChange(record.asset, 'slippage_pct', v ?? 0)
          }
          formatter={(v) => `${((v ?? 0) * 100).toFixed(3)}%`}
          parser={(v) => parseFloat(v?.replace('%', '') ?? '0') / 100}
          style={{ width: 90 }}
        />
      ),
    },
  ];

  return (
    <>
      {assetNames.length === 0 ? (
        <Empty
          description="请先上传数据文件 / Please upload data files first"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <>
          <Alert
            message="已上传资产，可按资产单独配置交易成本，或使用默认值"
            description={`${assetNames.length} 个资产已就绪 / ${assetNames.length} assets ready`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            action={
              <Button
                size="small"
                type="link"
                onClick={handleApplyToAll}
              >
                全部重置 / Reset All
              </Button>
            }
          />

          <Collapse defaultActiveKey={['1', '2']}>
            <Panel header="默认成本 / Default Costs" key="1">
              <Row gutter={24}>
                <Col span={6}>
                  <Form.Item label="买入% / Buy%">
                    <InputNumber
                      size="small"
                      min={0}
                      max={0.1}
                      step={0.0001}
                      value={DEFAULT_TRANSACTION_COST.buy_cost_pct}
                      formatter={(v) =>
                        `${((v ?? 0) * 100).toFixed(2)}%`
                      }
                      parser={(v) =>
                        parseFloat(v?.replace('%', '') ?? '0') / 100
                      }
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="卖出% / Sell%">
                    <InputNumber
                      size="small"
                      min={0}
                      max={0.1}
                      step={0.0001}
                      value={DEFAULT_TRANSACTION_COST.sell_cost_pct}
                      formatter={(v) =>
                        `${((v ?? 0) * 100).toFixed(2)}%`
                      }
                      parser={(v) =>
                        parseFloat(v?.replace('%', '') ?? '0') / 100
                      }
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="买入固定 / Buy Fixed">
                    <InputNumber
                      size="small"
                      min={0}
                      max={100}
                      step={0.5}
                      value={DEFAULT_TRANSACTION_COST.buy_cost_fixed}
                      formatter={(v) => `¥${(v ?? 0).toFixed(2)}`}
                      parser={(v) =>
                        parseFloat(v?.replace('¥', '') ?? '0')
                      }
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="滑点% / Slippage">
                    <InputNumber
                      size="small"
                      min={0}
                      max={0.05}
                      step={0.0001}
                      value={DEFAULT_TRANSACTION_COST.slippage_pct}
                      formatter={(v) =>
                        `${((v ?? 0) * 100).toFixed(3)}%`
                      }
                      parser={(v) =>
                        parseFloat(v?.replace('%', '') ?? '0') / 100
                      }
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>

            <Panel
              header={`按资产配置 / Per-Asset (${assetNames.length})`}
              key="2"
            >
              <Table
                dataSource={assetNames.map((asset) => ({
                  asset,
                  key: asset,
                }))}
                columns={transactionCostColumns}
                pagination={false}
                size="small"
                scroll={{ x: 500 }}
              />
            </Panel>
          </Collapse>
        </>
      )}
    </>
  );
};

/** Backtest parameters configuration panel section */
const BacktestSection: React.FC = () => {
  const { uploadedFiles, backtestConfig, setBacktestConfig } = useAppStore();
  const assetNames = uploadedFiles.map((f) => f.asset_name);

  return (
    <Form layout="vertical" size="small">
      <Row gutter={24}>
        <Col span={12}>
          <Form.Item label="初始资金 / Initial Value">
            <InputNumber
              prefix={<DollarOutlined />}
              min={10000}
              max={1000000000}
              step={10000}
              value={backtestConfig.initial_value}
              onChange={(v) =>
                setBacktestConfig({
                  ...backtestConfig,
                  initial_value: v ?? 1000000,
                })
              }
              formatter={(v) => `$${(v ?? 0).toLocaleString()}`}
              parser={(v) =>
                Number(v?.replace(/\$\s?|(,*)/g, ''))
              }
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="再平衡频率 / Rebalance Frequency">
            <Select
              value={backtestConfig.rebalance_freq}
              onChange={(v) =>
                setBacktestConfig({
                  ...backtestConfig,
                  rebalance_freq: v,
                })
              }
              options={REBALANCE_FREQ_OPTIONS}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={24}>
        <Col span={12}>
          <Form.Item label="基准资产 / Baseline Asset">
            <Select
              value={backtestConfig.baseline_asset || undefined}
              onChange={(v) =>
                setBacktestConfig({
                  ...backtestConfig,
                  baseline_asset: v,
                })
              }
              placeholder="选择基准 / Select baseline"
              allowClear
              options={assetNames.map((name) => ({
                value: name,
                label: name,
              }))}
            />
          </Form.Item>
        </Col>
      </Row>

      <Divider />

      <Form.Item label="滚动权重 / Rolling Weights">
        <Space>
          <Switch
            checked={backtestConfig.use_rolling_weights}
            onChange={(checked) =>
              setBacktestConfig({
                ...backtestConfig,
                use_rolling_weights: checked,
              })
            }
          />
          <Text type="secondary">
            动态调整权重 / Dynamically adjust weights
          </Text>
        </Space>
      </Form.Item>

      {backtestConfig.use_rolling_weights && (
        <>
          <Form.Item label="窗口类型 / Window Type">
            <Space>
              <Tag
                color={backtestConfig.use_fixed_window ? 'blue' : 'default'}
                style={{ cursor: 'pointer' }}
                onClick={() =>
                  setBacktestConfig({
                    ...backtestConfig,
                    use_fixed_window: true,
                  })
                }
              >
                固定窗口 / Fixed
              </Tag>
              <Tag
                color={!backtestConfig.use_fixed_window ? 'blue' : 'default'}
                style={{ cursor: 'pointer' }}
                onClick={() =>
                  setBacktestConfig({
                    ...backtestConfig,
                    use_fixed_window: false,
                  })
                }
              >
                累计窗口 / Cumulative
              </Tag>
            </Space>
          </Form.Item>

          {backtestConfig.use_fixed_window && (
            <Form.Item label="滚动窗口 / Rolling Window">
              <Row gutter={16}>
                <Col span={18}>
                  <Slider
                    min={30}
                    max={1000}
                    value={backtestConfig.rolling_window}
                    onChange={(v) =>
                      setBacktestConfig({
                        ...backtestConfig,
                        rolling_window: v,
                      })
                    }
                    marks={{
                      30: '30',
                      126: '6M',
                      252: '1Y',
                      504: '2Y',
                      1000: '1000',
                    }}
                  />
                </Col>
                <Col span={6}>
                  <InputNumber
                    min={30}
                    max={1000}
                    value={backtestConfig.rolling_window}
                    onChange={(v) =>
                      setBacktestConfig({
                        ...backtestConfig,
                        rolling_window: v ?? 252,
                      })
                    }
                    style={{ width: '100%' }}
                  />
                </Col>
              </Row>
            </Form.Item>
          )}
        </>
      )}
    </Form>
  );
};

/**
 * ConfigPanel - Unified configuration panel with type-based rendering
 */
const ConfigPanel: React.FC<ConfigPanelProps> = ({ type }) => {
  const renderContent = () => {
    switch (type) {
      case 'weighting':
        return (
          <Card
            title={
              <Space>
                <SettingOutlined />
                <span>权重配置 / Weighting Configuration</span>
              </Space>
            }
          >
            <WeightingSection />
          </Card>
        );
      case 'costs':
        return (
          <Card
            title={
              <Space>
                <PercentageOutlined />
                <span>交易成本 / Transaction Costs</span>
              </Space>
            }
          >
            <CostsSection />
          </Card>
        );
      case 'backtest':
        return (
          <>
            <Card
              title={
                <Space>
                  <ClockCircleOutlined />
                  <span>回测参数 / Backtest Parameters</span>
                </Space>
              }
            >
              <BacktestSection />
            </Card>
            <Card
              style={{ marginTop: 16 }}
              title={
                <Space>
                  <SettingOutlined />
                  <span>权重配置确认 / Weighting Config Summary</span>
                </Space>
              }
            >
              <WeightingSection />
            </Card>
            <Card
              style={{ marginTop: 16 }}
              title={
                <Space>
                  <PercentageOutlined />
                  <span>交易成本确认 / Cost Summary</span>
                </Space>
              }
            >
              <CostsSection />
            </Card>
          </>
        );
      default:
        return null;
    }
  };

  return <div className="config-panel">{renderContent()}</div>;
};

export default ConfigPanel;
