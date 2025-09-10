import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { UploadFile } from './hooks/useFileUpload';
import { formatFileSize, getFileIcon } from './FileValidator';

interface UploadProgressProps {
  file: UploadFile;
  onCancel?: () => void;
  onRetry?: () => void;
  onRemove?: () => void;
  className?: string;
}

/**
 * Upload progress indicator for individual files
 */
export const UploadProgress: React.FC<UploadProgressProps> = ({
  file,
  onCancel,
  onRetry,
  onRemove,
  className,
}) => {
  const getStatusColor = () => {
    switch (file.status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'uploading':
        return 'primary';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = () => {
    switch (file.status) {
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'cancelled':
        return <CancelIcon color="warning" fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (file.status) {
      case 'pending':
        return 'Waiting...';
      case 'uploading':
        return `Uploading... ${file.progress}%`;
      case 'success':
        return 'Uploaded';
      case 'error':
        return file.error || 'Failed';
      case 'cancelled':
        return 'Cancelled';
      default:
        return '';
    }
  };

  return (
    <Box
      className={className}
      sx={{
        p: 2,
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        bgcolor: 'background.paper',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        {/* File icon */}
        <Typography variant="h6" component="span">
          {getFileIcon(file.name)}
        </Typography>

        {/* File info */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{
              fontWeight: 500,
              mb: 0.5,
            }}
          >
            {file.name}
          </Typography>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <Typography variant="caption" color="textSecondary">
              {formatFileSize(file.size)}
            </Typography>

            <Chip
              label={getStatusText()}
              size="small"
              color={getStatusColor()}
              icon={getStatusIcon()}
              sx={{ height: 20 }}
            />
          </Box>
        </Box>

        {/* Action buttons */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {file.status === 'uploading' && onCancel && (
            <IconButton
              size="small"
              onClick={onCancel}
              title="Cancel upload"
            >
              <CancelIcon fontSize="small" />
            </IconButton>
          )}

          {(file.status === 'error' || file.status === 'cancelled') && onRetry && (
            <IconButton
              size="small"
              onClick={onRetry}
              title="Retry upload"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          )}

          {file.status !== 'uploading' && onRemove && (
            <IconButton
              size="small"
              onClick={onRemove}
              title="Remove file"
            >
              <CancelIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Progress bar */}
      {file.status === 'uploading' && (
        <Box sx={{ mt: 1 }}>
          <LinearProgress
            variant="determinate"
            value={file.progress}
            sx={{ height: 4, borderRadius: 2 }}
          />
        </Box>
      )}

      {/* Error message */}
      {file.status === 'error' && file.error && (
        <Typography
          variant="caption"
          color="error"
          sx={{ mt: 1, display: 'block' }}
        >
          {file.error}
        </Typography>
      )}

      {/* Success message with timestamp */}
      {file.status === 'success' && file.uploadedAt && (
        <Typography
          variant="caption"
          color="success.main"
          sx={{ mt: 1, display: 'block' }}
        >
          Uploaded at {file.uploadedAt.toLocaleTimeString()}
        </Typography>
      )}
    </Box>
  );
};

export default UploadProgress;