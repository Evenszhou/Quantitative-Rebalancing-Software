// ============================================================================
// Quant Portfolio Rebalancing App - Main Application
// ============================================================================

import React from 'react';
import { Layout, Steps, Button, Space, Typography } from 'antd';
import {
  CloudUploadOutlined,
  PieChartOutlined,
  DollarOutlined,
  LineChartOutlined,
  DownloadOutlined,
  RotateLeftOutlined,
} from '@ant-design/icons';
import FileUpload from './components/FileUpload';
import ConfigPanel from './components/ConfigPanel';
import ResultDisplay from './components/ResultDisplay';
import { useAppStore } from './store/useAppStore';
import { WorkflowStep } from './types';
import { runBacktest as runBacktestApi } from './services/api';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

/**
 * Main application component with step-based workflow navigation
 */
const App: React.FC = () => {
  const {
    currentStep,
    setCurrentStep,
    uploadedFiles,
    backtestConfig,
    setBacktestResult,
    isRunningBacktest,
    setIsRunningBacktest,
    backtestResult,
    resetAll,
  } = useAppStore();

  /**
   * Navigate to next step with validation
   */
  const goNext = () => {
    if (currentStep < WorkflowStep.RESULTS) {
      setCurrentStep((currentStep + 1) as WorkflowStep);
    }
  };

  /**
   * Navigate to previous step
   */
  const goPrev = () => {
    if (currentStep > WorkflowStep.UPLOAD) {
      setCurrentStep((currentStep - 1) as WorkflowStep);
    }
  };

  /**
   * Run backtest with current configuration
   */
  const handleRunBacktest = async () => {
    if (uploadedFiles.length === 0) {
      return;
    }
    setIsRunningBacktest(true);
    try {
      const fileIds = uploadedFiles.map((f) => f.file_id);
      const result = await runBacktestApi(fileIds, backtestConfig);
      setBacktestResult(result);
      setCurrentStep(WorkflowStep.RESULTS);
    } catch {
      // Error already handled by API interceptor
    } finally {
      setIsRunningBacktest(false);
    }
  };

  /** Step definitions */
  const stepItems = [
    {
      title: '数据上传',
      description: 'Upload Data',
      icon: <CloudUploadOutlined />,
    },
    {
      title: '配权设置',
      description: 'Weighting',
      icon: <PieChartOutlined />,
    },
    {
      title: '交易成本',
      description: 'Costs',
      icon: <DollarOutlined />,
    },
    {
      title: '回测分析',
      description: 'Backtest',
      icon: <LineChartOutlined />,
    },
    {
      title: '结果导出',
      description: 'Results',
      icon: <DownloadOutlined />,
    },
  ];

  /** Render current step content */
  const renderStepContent = () => {
    switch (currentStep) {
      case WorkflowStep.UPLOAD:
        return <FileUpload />;
      case WorkflowStep.WEIGHTING:
        return <ConfigPanel type="weighting" />;
      case WorkflowStep.COSTS:
        return <ConfigPanel type="costs" />;
      case WorkflowStep.BACKTEST:
        return <ConfigPanel type="backtest" />;
      case WorkflowStep.RESULTS:
        return <ResultDisplay />;
      default:
        return <FileUpload />;
    }
  };

  return (
    <Layout className="app-layout">
      {/* Header */}
      <Header className="app-header">
        <div className="header-content">
          <Title level={4} style={{ margin: 0, color: '#fff' }}>
            📊 量化组合再平衡系统
          </Title>
          <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13 }}>
            Quantitative Portfolio Rebalancing System
          </Text>
        </div>
      </Header>

      <Layout>
        {/* Sidebar with steps */}
        <Sider
          width={240}
          className="app-sider"
          breakpoint="lg"
          collapsedWidth={0}
        >
          <div className="sider-steps">
            <Steps
              direction="vertical"
              current={currentStep}
              items={stepItems}
              onChange={(step) => setCurrentStep(step as WorkflowStep)}
              style={{ marginTop: 24 }}
            />
          </div>

          {/* Reset button at bottom of sidebar */}
          <div className="sider-footer">
            <Button
              icon={<RotateLeftOutlined />}
              onClick={resetAll}
              block
              type="text"
              danger
            >
              重置 / Reset
            </Button>
          </div>
        </Sider>

        {/* Main content area */}
        <Layout>
          <Content className="app-content">
            <div className="content-wrapper">
              {/* Step title bar */}
              <div className="step-header">
                <Title level={5}>
                  步骤 {currentStep + 1}：{stepItems[currentStep].title}
                </Title>
                <Text type="secondary">{stepItems[currentStep].description}</Text>
              </div>

              {/* Step content */}
              <div className="step-content">{renderStepContent()}</div>

              {/* Navigation footer */}
              <div className="step-footer">
                <Space>
                  <Button
                    onClick={goPrev}
                    disabled={currentStep === WorkflowStep.UPLOAD}
                  >
                    上一步 / Previous
                  </Button>

                  {currentStep === WorkflowStep.BACKTEST && (
                    <Button
                      type="primary"
                      loading={isRunningBacktest}
                      onClick={handleRunBacktest}
                      disabled={uploadedFiles.length === 0}
                      icon={<LineChartOutlined />}
                    >
                      {isRunningBacktest ? '回测中...' : '运行回测 / Run Backtest'}
                    </Button>
                  )}

                  {currentStep === WorkflowStep.RESULTS && backtestResult && (
                    <Button type="primary" onClick={() => {}}>
                      导出报告 / Export
                    </Button>
                  )}

                  {currentStep < WorkflowStep.RESULTS &&
                    currentStep !== WorkflowStep.BACKTEST && (
                      <Button
                        type="primary"
                        onClick={goNext}
                        disabled={
                          currentStep === WorkflowStep.UPLOAD &&
                          uploadedFiles.length === 0
                        }
                      >
                        下一步 / Next
                      </Button>
                    )}
                </Space>
              </div>
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default App;
