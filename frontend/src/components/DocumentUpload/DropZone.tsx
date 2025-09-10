import React, { useCallback } from 'react';
import { useDropzone, DropzoneOptions } from 'react-dropzone';
import { Box, Typography, Paper, useTheme } from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import { SUPPORTED_EXTENSIONS, DEFAULT_MAX_FILE_SIZE } from './FileValidator';

interface DropZoneProps {
  onDrop: (files: File[]) => void;
  maxSize?: number;
  maxFiles?: number;
  accept?: Record<string, string[]>;
  disabled?: boolean;
  className?: string;
}

/**
 * Drag and drop zone for file uploads
 */
export const DropZone: React.FC<DropZoneProps> = ({
  onDrop,
  maxSize = DEFAULT_MAX_FILE_SIZE,
  maxFiles = 10,
  accept,
  disabled = false,
  className,
}) => {
  const theme = useTheme();

  // Default accept configuration
  const defaultAccept = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md', '.markdown'],
    'text/csv': ['.csv'],
  };

  const handleDrop = useCallback((acceptedFiles: File[]) => {
    if (!disabled) {
      onDrop(acceptedFiles);
    }
  }, [onDrop, disabled]);

  const dropzoneOptions: DropzoneOptions = {
    onDrop: handleDrop,
    maxSize,
    maxFiles,
    accept: accept || defaultAccept,
    disabled,
    multiple: true,
  };

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    isDragAccept,
  } = useDropzone(dropzoneOptions);

  // Determine border color based on drag state
  const getBorderColor = () => {
    if (disabled) return theme.palette.action.disabled;
    if (isDragReject) return theme.palette.error.main;
    if (isDragAccept) return theme.palette.success.main;
    if (isDragActive) return theme.palette.primary.main;
    return theme.palette.divider;
  };

  // Determine background color based on drag state
  const getBackgroundColor = () => {
    if (disabled) return theme.palette.action.disabledBackground;
    if (isDragReject) return `${theme.palette.error.main}10`;
    if (isDragAccept) return `${theme.palette.success.main}10`;
    if (isDragActive) return `${theme.palette.primary.main}10`;
    return theme.palette.background.default;
  };

  return (
    <Paper
      {...getRootProps()}
      className={className}
      elevation={0}
      sx={{
        p: 4,
        border: 2,
        borderStyle: 'dashed',
        borderColor: getBorderColor(),
        backgroundColor: getBackgroundColor(),
        borderRadius: 2,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: disabled ? undefined : theme.palette.primary.main,
          backgroundColor: disabled ? undefined : `${theme.palette.primary.main}05`,
        },
      }}
    >
      <input {...getInputProps()} />
      
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <CloudUploadIcon
          sx={{
            fontSize: 64,
            color: isDragReject
              ? theme.palette.error.main
              : isDragAccept
              ? theme.palette.success.main
              : isDragActive
              ? theme.palette.primary.main
              : theme.palette.action.active,
            transition: 'color 0.3s ease',
          }}
        />

        <Typography
          variant="h6"
          align="center"
          color={
            isDragReject
              ? 'error'
              : isDragActive
              ? 'primary'
              : 'textPrimary'
          }
        >
          {isDragReject
            ? 'File type not supported!'
            : isDragActive
            ? 'Drop files here...'
            : 'Drag & drop files here, or click to select'}
        </Typography>

        <Typography
          variant="body2"
          color="textSecondary"
          align="center"
        >
          Supported formats: {SUPPORTED_EXTENSIONS.join(', ')}
        </Typography>

        <Typography
          variant="caption"
          color="textSecondary"
          align="center"
        >
          Maximum file size: {Math.round(maxSize / (1024 * 1024))}MB
          {maxFiles > 1 && ` • Up to ${maxFiles} files`}
        </Typography>

        {disabled && (
          <Typography
            variant="body2"
            color="error"
            align="center"
            sx={{ mt: 1 }}
          >
            Upload is currently disabled
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default DropZone;