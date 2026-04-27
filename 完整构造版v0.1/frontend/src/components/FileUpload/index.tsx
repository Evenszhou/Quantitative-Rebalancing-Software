// ============================================================================
// FileUpload - File Upload Component
// Supports Excel (.xlsx, .xls) and CSV files with drag-and-drop
// ============================================================================

import React, { useState } from 'react';
import {
  Upload,
  message,
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Popconfirm,
  Empty,
  Spin,
} from 'antd';
import {
  InboxOutlined,
  DeleteOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import type { UploadProps, UploadFile } from 'antd/es/upload/interface';
import { uploadFile, deleteFile } from '@/services/api';
import { useAppStore } from '@/store/useAppStore';
import type { UploadedFile } from '@/types';

const { Dragger } = Upload;
const { Text, Title } = Typography;

const FileUpload: React.FC = () => {
  const {
    uploadedFiles,
    addUploadedFile,
    removeUploadedFile,
    isUploading,
    setIsUploading,
  } = useAppStore();

  const [fileList, setFileList] = useState<UploadFile[]>([]);

  /**
   * Upload a single file to the backend
   */
  const handleUpload = async (file: File): Promise<boolean> => {
    setIsUploading(true);
    try {
      const result = await uploadFile(file);
      addUploadedFile(result);
      message.success(`${file.name} 上传成功`);
      return true;
    } catch {
      message.error(`${file.name} 上传失败`);
      return false;
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Delete an uploaded file from the backend and local state
   */
  const handleDelete = async (fileId: string, fileName: string) => {
    try {
      await deleteFile(fileId);
      removeUploadedFile(fileId);
      setFileList((prev) => prev.filter((f) => f.uid !== fileId));
      message.success(`${fileName} 已删除`);
    } catch {
      message.error('删除失败');
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.xlsx,.xls,.csv',
    fileList,
    beforeUpload: (file) => {
      const isValidType =
        file.name.endsWith('.xlsx') ||
        file.name.endsWith('.xls') ||
        file.name.endsWith('.csv');

      if (!isValidType) {
        message.error('只支持 Excel (.xlsx, .xls) 和 CSV 文件');
        return Upload.LIST_IGNORE;
      }

      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB');
        return Upload.LIST_IGNORE;
      }

      handleUpload(file);
      return false; // Prevent auto upload, we handle it manually
    },
    onChange: (info) => {
      setFileList(info.fileList);
    },
    onRemove: (file) => {
      const uploadedFile = uploadedFiles.find((f) => f.asset_name === file.name);
      if (uploadedFile) {
        handleDelete(uploadedFile.file_id, file.name);
      }
    },
  };

  /** Table columns for uploaded files list */
  const columns = [
    {
      title: '文件名',
      dataIndex: 'asset_name',
      key: 'asset_name',
      render: (name: string) => (
        <Space>
          {name.endsWith('.csv') ? <FileTextOutlined /> : <FileExcelOutlined />}
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '数据行数',
      dataIndex: 'rows',
      key: 'rows',
      render: (rows: number) => <Tag color="blue">{rows.toLocaleString()}</Tag>,
      align: 'center' as const,
    },
    {
      title: '列名',
      dataIndex: 'columns',
      key: 'columns',
      render: (columns: string[]) => (
        <Space size={[0, 4]} wrap>
          {columns.slice(0, 4).map((col) => (
            <Tag key={col} color="default">
              {col}
            </Tag>
          ))}
          {columns.length > 4 && (
            <Tag color="default">+{columns.length - 4}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      align: 'center' as const,
      render: (_: unknown, record: UploadedFile) => (
        <Popconfirm
          title="确定删除此文件？"
          onConfirm={() => handleDelete(record.file_id, record.asset_name)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div className="file-upload-container">
      {/* Upload area */}
      <Card className="upload-card">
        <Spin spinning={isUploading} tip="上传中...">
          <Dragger {...uploadProps} className="upload-dragger">
            <p className="ant-upload-drag-icon">
              <CloudUploadOutlined style={{ fontSize: 48, color: '#1677ff' }} />
            </p>
            <Title level={4}>点击或拖拽文件到此区域上传</Title>
            <Text type="secondary">
              支持 Excel (.xlsx, .xls) 和 CSV 文件，单文件不超过 50MB
            </Text>
          </Dragger>
        </Spin>
      </Card>

      {/* Uploaded files list */}
      <Card
        className="files-card"
        title={
          <Space>
            <InboxOutlined />
            <span>已上传文件</span>
            <Tag color="blue">{uploadedFiles.length}</Tag>
          </Space>
        }
      >
        {uploadedFiles.length === 0 ? (
          <Empty
            description="暂无上传文件"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Table
            dataSource={uploadedFiles}
            columns={columns}
            rowKey="file_id"
            pagination={false}
            size="small"
            className="files-table"
          />
        )}
      </Card>
    </div>
  );
};

export default FileUpload;
