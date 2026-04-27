// ============================================================================
// Zustand Store - Application State Management
// ============================================================================

import { create } from 'zustand';
import type {
  AppState,
  BacktestConfig,
  TransactionCost,
  WorkflowStep,
} from '@/types';
import {
  DEFAULT_BACKTEST_CONFIG,
} from '@/types';

const defaultConfig: BacktestConfig = { ...DEFAULT_BACKTEST_CONFIG };

export const useAppStore = create<AppState>((set) => ({
  currentStep: 0 as WorkflowStep,
  setCurrentStep: (step) => set({ currentStep: step }),

  uploadedFiles: [],
  setUploadedFiles: (files) => set({ uploadedFiles: files }),
  addUploadedFile: (file) =>
    set((state) => ({
      uploadedFiles: [...state.uploadedFiles, file],
    })),
  removeUploadedFile: (fileId) =>
    set((state) => ({
      uploadedFiles: state.uploadedFiles.filter((f) => f.file_id !== fileId),
    })),
  clearUploadedFiles: () => set({ uploadedFiles: [] }),

  weightsResult: null,
  setWeightsResult: (result) => set({ weightsResult: result }),

  backtestConfig: { ...defaultConfig },
  setBacktestConfig: (config) => set({ backtestConfig: config }),
  updateWeightingConfig: (config) =>
    set((state) => ({
      backtestConfig: {
        ...state.backtestConfig,
        weighting_config: {
          ...state.backtestConfig.weighting_config,
          ...config,
        },
      },
    })),
  updateTransactionCosts: (asset, costs) =>
    set((state) => ({
      backtestConfig: {
        ...state.backtestConfig,
        transaction_costs: {
          ...state.backtestConfig.transaction_costs,
          [asset]: costs,
        },
      },
    })),
  setDefaultTransactionCosts: (costs) =>
    set((state) => {
      const newCosts: Record<string, TransactionCost> = {
        default: costs,
      };
      state.uploadedFiles.forEach((file) => {
        newCosts[file.asset_name] = { ...costs };
      });
      return {
        backtestConfig: {
          ...state.backtestConfig,
          transaction_costs: newCosts,
        },
      };
    }),

  backtestResult: null,
  setBacktestResult: (result) => set({ backtestResult: result }),

  isUploading: false,
  setIsUploading: (loading) => set({ isUploading: loading }),
  isCalculatingWeights: false,
  setIsCalculatingWeights: (loading) => set({ isCalculatingWeights: loading }),
  isRunningBacktest: false,
  setIsRunningBacktest: (loading) => set({ isRunningBacktest: loading }),

  resetAll: () =>
    set({
      currentStep: 0,
      uploadedFiles: [],
      weightsResult: null,
      backtestConfig: { ...defaultConfig },
      backtestResult: null,
      isUploading: false,
      isCalculatingWeights: false,
      isRunningBacktest: false,
    }),
}));
