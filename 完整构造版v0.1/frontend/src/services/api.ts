import axios, { AxiosError } from 'axios';
import { message } from 'antd';
import type {
  UploadedFile,
  WeightingConfig,
  BacktestConfig,
  WeightsResult,
  BacktestResult,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
    message.error(errorMsg);
    return Promise.reject(error);
  }
);

export const uploadFile = async (file: File): Promise<UploadedFile> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadedFile>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000,
  });

  return response.data;
};

export const uploadFiles = async (files: File[]): Promise<UploadedFile[]> => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await api.post<UploadedFile[]>('/upload/batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000,
  });

  return response.data;
};

export const deleteFile = async (fileId: string): Promise<void> => {
  await api.delete(`/files/${fileId}`);
};

export const getUploadedFiles = async (): Promise<UploadedFile[]> => {
  const response = await api.get<UploadedFile[]>('/files');
  return response.data;
};

export const calculateWeights = async (
  fileIds: string[],
  config: WeightingConfig
): Promise<WeightsResult> => {
  const response = await api.post<WeightsResult>('/weights/calculate', {
    file_ids: fileIds,
    config,
  });
  return response.data;
};

export const runBacktest = async (
  fileIds: string[],
  config: BacktestConfig
): Promise<BacktestResult> => {
  const response = await api.post<BacktestResult>('/backtest/run', {
    file_ids: fileIds,
    config,
  }, {
    timeout: 300000,
  });
  return response.data;
};

export const getBacktestStatus = async (taskId: string): Promise<{
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  result?: BacktestResult;
}> => {
  const response = await api.get(`/backtest/status/${taskId}`);
  return response.data;
};

export const exportExcel = async (taskId: string): Promise<Blob> => {
  const response = await api.get(`/backtest/export/${taskId}`, {
    responseType: 'blob',
    timeout: 60000,
  });
  return response.data;
};

export const downloadExport = async (taskId: string, filename?: string): Promise<void> => {
  const blob = await exportExcel(taskId);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || `backtest_result_${taskId}.xlsx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const getAssetList = async (): Promise<string[]> => {
  const response = await api.get<string[]>('/assets');
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await api.get<{ status: string }>('/health');
  return response.data;
};

export default api;
