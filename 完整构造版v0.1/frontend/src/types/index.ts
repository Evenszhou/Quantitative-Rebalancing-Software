// ============================================================================
// Quant Portfolio Rebalancing App - TypeScript Types
// ============================================================================

/**
 * Weighting method options for portfolio optimization
 */
export enum WeightingMethod {
  EQUAL = 'equal_weight',
  RISK_PARITY = 'risk_parity',
  MIN_VARIANCE = 'minimum_variance',
  MAX_SHARPE = 'maximum_sharpe'
}

/**
 * Rebalancing frequency options
 */
export enum RebalanceFreq {
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  YEARLY = 'yearly',
  NONE = 'none'
}

/**
 * Transaction cost configuration for a single asset or default
 */
export interface TransactionCost {
  buy_cost_pct: number;
  sell_cost_pct: number;
  buy_cost_fixed: number;
  sell_cost_fixed: number;
  slippage_pct: number;
}

/**
 * Uploaded file metadata returned from server
 */
export interface UploadedFile {
  file_id: string;
  asset_name: string;
  rows: number;
  columns: string[];
}

/**
 * Weighting configuration for portfolio optimization
 */
export interface WeightingConfig {
  method: WeightingMethod;
  warmup_period: number;
  risk_free_rate: number;
  allow_short: boolean;
  selected_assets?: string[];
}

/**
 * Complete backtest configuration
 */
export interface BacktestConfig {
  initial_value: number;
  rebalance_freq: RebalanceFreq;
  baseline_asset: string;
  use_rolling_weights: boolean;
  use_fixed_window: boolean;
  rolling_window: number;
  transaction_costs: Record<string, TransactionCost>;
  weighting_config: WeightingConfig;
}

/**
 * Portfolio weights result from optimization
 */
export interface WeightsResult {
  assets: string[];
  weights: Record<string, number>;
  metrics: {
    annual_return: number;
    annual_volatility: number;
    sharpe_ratio: number;
  };
}

/**
 * Backtest performance metrics
 */
export interface BacktestMetrics {
  annual_return: number;
  annual_volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  calmar_ratio: number;
  sortino_ratio: number;
  baseline_return: number;
  excess_return: number;
  information_ratio: number;
  win_rate: number;
  total_trades: number;
  total_transaction_cost: number;
}

/**
 * Time series data point for returns
 */
export interface ReturnSeriesPoint {
  portfolio: number;
  baseline: number;
}

/**
 * Trade log entry
 */
export interface TradeLogEntry {
  date: string;
  type: string;
  total_cost: number;
}

/**
 * Complete backtest result
 */
export interface BacktestResult {
  task_id: string;
  metrics: BacktestMetrics;
  returns_series: Record<string, ReturnSeriesPoint>;
  position_series: Record<string, Record<string, number>>;
  trade_log: TradeLogEntry[];
}

/**
 * Default transaction cost configuration
 */
export const DEFAULT_TRANSACTION_COST: TransactionCost = {
  buy_cost_pct: 0.001,
  sell_cost_pct: 0.001,
  buy_cost_fixed: 0,
  sell_cost_fixed: 0,
  slippage_pct: 0.0005,
};

/**
 * Default weighting configuration
 */
export const DEFAULT_WEIGHTING_CONFIG: WeightingConfig = {
  method: WeightingMethod.EQUAL,
  warmup_period: 252,
  risk_free_rate: 0.02,
  allow_short: false,
};

/**
 * Default backtest configuration
 */
export const DEFAULT_BACKTEST_CONFIG: BacktestConfig = {
  initial_value: 1000000,
  rebalance_freq: RebalanceFreq.QUARTERLY,
  baseline_asset: '',
  use_rolling_weights: false,
  use_fixed_window: true,
  rolling_window: 252,
  transaction_costs: {},
  weighting_config: DEFAULT_WEIGHTING_CONFIG,
};

/**
 * Workflow step identifiers
 */
export enum WorkflowStep {
  UPLOAD = 0,
  WEIGHTING = 1,
  COSTS = 2,
  BACKTEST = 3,
  RESULTS = 4,
}

/**
 * App state interface for Zustand store
 */
export interface AppState {
  // Workflow state
  currentStep: WorkflowStep;
  setCurrentStep: (step: WorkflowStep) => void;
  
  // Uploaded files
  uploadedFiles: UploadedFile[];
  setUploadedFiles: (files: UploadedFile[]) => void;
  addUploadedFile: (file: UploadedFile) => void;
  removeUploadedFile: (fileId: string) => void;
  clearUploadedFiles: () => void;
  
  // Calculated weights
  weightsResult: WeightsResult | null;
  setWeightsResult: (result: WeightsResult | null) => void;
  
  // Backtest configuration
  backtestConfig: BacktestConfig;
  setBacktestConfig: (config: BacktestConfig) => void;
  updateWeightingConfig: (config: Partial<WeightingConfig>) => void;
  updateTransactionCosts: (asset: string, costs: TransactionCost) => void;
  setDefaultTransactionCosts: (costs: TransactionCost) => void;
  
  // Backtest results
  backtestResult: BacktestResult | null;
  setBacktestResult: (result: BacktestResult | null) => void;
  
  // Loading states
  isUploading: boolean;
  setIsUploading: (loading: boolean) => void;
  isCalculatingWeights: boolean;
  setIsCalculatingWeights: (loading: boolean) => void;
  isRunningBacktest: boolean;
  setIsRunningBacktest: (loading: boolean) => void;
  
  // Reset
  resetAll: () => void;
}
