import React, { useCallback, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Description as DocumentIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { DropZone } from './DropZone';
import { FileList } from './FileList';
import { useFileUpload } from './hooks/useFileUpload';

interface DocumentUploadProps {
  endpoint?: string;
  maxFiles?: number;
  maxSize?: number;
  allowedTypes?: string[];
  autoUpload?: boolean;
  onUploadComplete?: (files: any[]) => void;
  onClose?: () => void;
  open?: boolean;
  embedded?: boolean;
  className?: string;
}

/**
 * Main document upload component
 * Can be used as a modal dialog or embedded component
 */
export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  endpoint,
  maxFiles = 10,
  maxSize,
  allowedTypes,
  autoUpload = false,
  onUploadComplete,
  onClose,
  open = true,
  embedded = false,
  className,
}) => {
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  const {
    files,
    isUploading,
    totalProgress,
    addFiles,
    removeFile,
    uploadFile,
    uploadAll,
    cancelUpload,
    cancelAll,
    clearAll,
    retryFailed,
  } = useFileUpload({
    endpoint,
    maxFiles,
    maxSize,
    allowedTypes,
    autoUpload,
    onSuccess: (file) => {
      setSnackbar({
        open: true,
        message: `${file.name} uploaded successfully`,
        severity: 'success',
      });
    },
    onError: (file, error) => {
      setSnackbar({
        open: true,
        message: `Failed to upload ${file.name}: ${error.message}`,
        severity: 'error',
      });
    },
  });

  const handleDrop = useCallback((droppedFiles: File[]) => {
    addFiles(droppedFiles);
    
    if (droppedFiles.length > 0) {
      setSnackbar({
        open: true,
        message: `Added ${droppedFiles.length} file(s) to upload queue`,
        severity: 'info',
      });
    }
  }, [addFiles]);

  const handleUploadComplete = useCallback(() => {
    const successfulFiles = files.filter(f => f.status === 'success');
    if (successfulFiles.length > 0 && onUploadComplete) {
      onUploadComplete(successfulFiles);
    }
    
    if (onClose) {
      onClose();
    }
  }, [files, onUploadComplete, onClose]);

  const handleRetryFile = useCallback((id: string) => {
    uploadFile(id);
  }, [uploadFile]);

  const content = (
    <Box className={className}>
      {/* Header for embedded mode */}
      {embedded && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 2,
          }}
        >
          <DocumentIcon color="primary" />
          <Typography variant="h6">Document Upload</Typography>
        </Box>
      )}

      {/* Drop zone */}
      <DropZone
        onDrop={handleDrop}
        maxSize={maxSize}
        maxFiles={maxFiles - files.length}
        disabled={isUploading || files.length >= maxFiles}
      />

      {/* File list */}
      <FileList
        files={files}
        isUploading={isUploading}
        totalProgress={totalProgress}
        onUploadAll={uploadAll}
        onCancelAll={cancelAll}
        onClearAll={clearAll}
        onRetryFailed={retryFailed}
        onRemoveFile={removeFile}
        onCancelFile={cancelUpload}
        onRetryFile={handleRetryFile}
      />

      {/* Info text */}
      {files.length === 0 && (
        <Typography
          variant="body2"
          color="textSecondary"
          align="center"
          sx={{ mt: 2 }}
        >
          Documents will be processed and added to your knowledge base after upload.
        </Typography>
      )}
    </Box>
  );

  // Render as dialog
  if (!embedded) {
    return (
      <>
        <Dialog
          open={open}
          onClose={onClose}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: { minHeight: 400 },
          }}
        >
          <DialogTitle>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DocumentIcon color="primary" />
                <Typography variant="h6">Upload Documents</Typography>
              </Box>
              {onClose && (
                <Button
                  onClick={onClose}
                  color="inherit"
                  size="small"
                  startIcon={<CloseIcon />}
                >
                  Close
                </Button>
              )}
            </Box>
          </DialogTitle>

          <DialogContent dividers>{content}</DialogContent>

          <DialogActions>
            <Button onClick={onClose} disabled={isUploading}>
              Cancel
            </Button>
            {files.length > 0 && (
              <Button
                variant="contained"
                onClick={handleUploadComplete}
                disabled={isUploading || files.some(f => f.status === 'pending')}
              >
                Done ({files.filter(f => f.status === 'success').length} uploaded)
              </Button>
            )}
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </>
    );
  }

  // Render as embedded component
  return (
    <Paper elevation={0} sx={{ p: 3 }}>
      {content}
    </Paper>
  );
};

export default DocumentUpload;