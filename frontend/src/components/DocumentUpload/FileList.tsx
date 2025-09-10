import React from 'react';
import {
  Box,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Collapse,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { TransitionGroup } from 'react-transition-group';
import { UploadFile } from './hooks/useFileUpload';
import { UploadProgress } from './UploadProgress';
import { formatFileSize } from './FileValidator';

interface FileListProps {
  files: UploadFile[];
  isUploading: boolean;
  totalProgress: number;
  onUploadAll?: () => void;
  onCancelAll?: () => void;
  onClearAll?: () => void;
  onRetryFailed?: () => void;
  onRemoveFile?: (id: string) => void;
  onCancelFile?: (id: string) => void;
  onRetryFile?: (id: string) => void;
  className?: string;
}

/**
 * File list component showing upload queue and progress
 */
export const FileList: React.FC<FileListProps> = ({
  files,
  isUploading,
  totalProgress,
  onUploadAll,
  onCancelAll,
  onClearAll,
  onRetryFailed,
  onRemoveFile,
  onCancelFile,
  onRetryFile,
  className,
}) => {
  // Calculate statistics
  const stats = {
    total: files.length,
    pending: files.filter(f => f.status === 'pending').length,
    uploading: files.filter(f => f.status === 'uploading').length,
    success: files.filter(f => f.status === 'success').length,
    failed: files.filter(f => f.status === 'error').length,
    cancelled: files.filter(f => f.status === 'cancelled').length,
    totalSize: files.reduce((sum, f) => sum + f.size, 0),
  };

  const hasFailedFiles = stats.failed > 0 || stats.cancelled > 0;
  const hasPendingFiles = stats.pending > 0;

  if (files.length === 0) {
    return null;
  }

  return (
    <Box className={className} sx={{ mt: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
        }}
      >
        <Box>
          <Typography variant="h6">
            Upload Queue ({stats.total} files)
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Total size: {formatFileSize(stats.totalSize)}
            {stats.success > 0 && ` • Uploaded: ${stats.success}`}
            {stats.failed > 0 && ` • Failed: ${stats.failed}`}
          </Typography>
        </Box>

        {/* Action buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          {hasPendingFiles && !isUploading && onUploadAll && (
            <Button
              variant="contained"
              size="small"
              startIcon={<UploadIcon />}
              onClick={onUploadAll}
            >
              Upload All ({stats.pending})
            </Button>
          )}

          {isUploading && onCancelAll && (
            <Button
              variant="outlined"
              size="small"
              color="warning"
              startIcon={<CancelIcon />}
              onClick={onCancelAll}
            >
              Cancel All
            </Button>
          )}

          {hasFailedFiles && !isUploading && onRetryFailed && (
            <Button
              variant="outlined"
              size="small"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={onRetryFailed}
            >
              Retry Failed ({stats.failed + stats.cancelled})
            </Button>
          )}

          {!isUploading && onClearAll && (
            <Button
              variant="outlined"
              size="small"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={onClearAll}
            >
              Clear All
            </Button>
          )}
        </Box>
      </Box>

      {/* Overall progress */}
      {isUploading && (
        <Box sx={{ mb: 2 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 1,
            }}
          >
            <Typography variant="body2">
              Overall Progress
            </Typography>
            <Typography variant="body2" color="primary">
              {Math.round(totalProgress)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={totalProgress}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
      )}

      {/* Status summary */}
      {stats.failed > 0 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {stats.failed} file{stats.failed > 1 ? 's' : ''} failed to upload.
          {onRetryFailed && ' Click "Retry Failed" to try again.'}
        </Alert>
      )}

      {stats.success === stats.total && stats.total > 0 && (
        <Alert severity="success" sx={{ mb: 2 }}>
          All files uploaded successfully!
        </Alert>
      )}

      {/* File list */}
      <TransitionGroup>
        {files.map(file => (
          <Collapse key={file.id}>
            <Box sx={{ mb: 1 }}>
              <UploadProgress
                file={file}
                onCancel={
                  file.status === 'uploading' && onCancelFile
                    ? () => onCancelFile(file.id)
                    : undefined
                }
                onRetry={
                  (file.status === 'error' || file.status === 'cancelled') && onRetryFile
                    ? () => onRetryFile(file.id)
                    : undefined
                }
                onRemove={
                  file.status !== 'uploading' && onRemoveFile
                    ? () => onRemoveFile(file.id)
                    : undefined
                }
              />
            </Box>
          </Collapse>
        ))}
      </TransitionGroup>
    </Box>
  );
};

export default FileList;