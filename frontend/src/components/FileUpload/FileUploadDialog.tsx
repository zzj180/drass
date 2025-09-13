import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  Alert,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
  Chip,
  Paper,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { authService } from '../../services/authService';
import { getApiUrl } from '../../config/config';

interface FileUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUploadComplete?: (files: UploadedFile[]) => void;
}

interface SelectedFile {
  file: File;
  purpose: 'knowledge_base' | 'business_context';
}

interface UploadedFile {
  id: string;
  name: string;
  purpose: 'knowledge_base' | 'business_context';
  status: 'success' | 'error';
  message?: string;
}

export const FileUploadDialog: React.FC<FileUploadDialogProps> = ({
  open,
  onClose,
  onUploadComplete,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [uploadPurpose, setUploadPurpose] = useState<'knowledge_base' | 'business_context'>('knowledge_base');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResults, setUploadResults] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    const newFiles: SelectedFile[] = Array.from(files).map(file => ({
      file,
      purpose: uploadPurpose,
    }));

    setSelectedFiles(prev => [...prev, ...newFiles]);
    setError(null);
  }, [uploadPurpose]);

  const handleRemoveFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadResults([]);
    setError(null);

    const results: UploadedFile[] = [];
    const totalFiles = selectedFiles.length;

    for (let i = 0; i < selectedFiles.length; i++) {
      const { file, purpose } = selectedFiles[i];
      setUploadProgress(((i + 1) / totalFiles) * 100);

      try {
        if (purpose === 'knowledge_base') {
          // Upload to knowledge base
          const formData = new FormData();
          formData.append('file', file);
          formData.append('name', file.name);
          formData.append('description', `Uploaded on ${new Date().toLocaleDateString()}`);

          const response = await fetch(`${getApiUrl('backendUrl')}/api/v1/documents/upload`, {
            method: 'POST',
            headers: {
              ...authService.getAuthHeaders(),
            },
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
          }

          const document = await response.json();

          // Process the document to add it to knowledge base
          const processResponse = await fetch(
            `${getApiUrl('backendUrl')}/api/v1/documents/${document.id}/process`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...authService.getAuthHeaders(),
              },
              body: JSON.stringify({
                chunk_size: 1000,
                chunk_overlap: 200,
              }),
            }
          );

          if (!processResponse.ok) {
            throw new Error('Failed to process document for knowledge base');
          }

          results.push({
            id: document.id,
            name: file.name,
            purpose,
            status: 'success',
            message: 'Successfully added to knowledge base',
          });
        } else {
          // For business context, we'll store it temporarily
          // In a real implementation, you might want to upload to a different endpoint
          results.push({
            id: `temp-${Date.now()}-${i}`,
            name: file.name,
            purpose,
            status: 'success',
            message: 'Ready to use as business context',
          });
        }
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error);
        results.push({
          id: `error-${Date.now()}-${i}`,
          name: file.name,
          purpose,
          status: 'error',
          message: error instanceof Error ? error.message : 'Upload failed',
        });
      }
    }

    setUploadResults(results);
    setIsUploading(false);
    setSelectedFiles([]);

    // Notify parent component
    if (onUploadComplete) {
      onUploadComplete(results);
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setSelectedFiles([]);
      setUploadResults([]);
      setError(null);
      setUploadProgress(0);
      onClose();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '500px' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Upload Files</Typography>
          <IconButton onClick={handleClose} disabled={isUploading}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {/* Upload Purpose Selection */}
        {selectedFiles.length === 0 && uploadResults.length === 0 && (
          <Box mb={3}>
            <FormControl component="fieldset">
              <FormLabel component="legend">Select Upload Purpose</FormLabel>
              <RadioGroup
                value={uploadPurpose}
                onChange={(e) => setUploadPurpose(e.target.value as 'knowledge_base' | 'business_context')}
              >
                <FormControlLabel
                  value="knowledge_base"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="body1">Knowledge Base</Typography>
                      <Typography variant="caption" color="textSecondary">
                        Add documents to the persistent knowledge base for long-term reference
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="business_context"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="body1">Business Context</Typography>
                      <Typography variant="caption" color="textSecondary">
                        Use documents as temporary context for current conversation
                      </Typography>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>
          </Box>
        )}

        {/* File Selection Area */}
        {!isUploading && uploadResults.length === 0 && (
          <Box>
            <Paper
              variant="outlined"
              sx={{
                p: 4,
                backgroundColor: 'background.default',
                borderStyle: 'dashed',
                borderWidth: 2,
                borderColor: 'divider',
                cursor: 'pointer',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '200px',
                '&:hover': {
                  backgroundColor: 'action.hover',
                  borderColor: 'primary.main',
                },
              }}
              component="label"
            >
              <input
                type="file"
                multiple
                hidden
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls"
              />

              {/* Upload Icon with positioning */}
              <Box
                sx={{
                  position: 'absolute',
                  top: '24px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  backgroundColor: 'action.selected',
                  borderRadius: '50%',
                  width: '80px',
                  height: '80px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <UploadIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
              </Box>

              {/* Text content */}
              <Box sx={{ mt: 10, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  Click to select files or drag and drop
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Supported formats: PDF, DOC, DOCX, TXT, MD, JSON, CSV, XLSX, XLS
                </Typography>
              </Box>

              {/* Purpose chip positioned at bottom left */}
              <Box
                sx={{
                  position: 'absolute',
                  bottom: '16px',
                  left: '16px',
                }}
              >
                <Chip
                  label={uploadPurpose === 'knowledge_base' ? 'Knowledge Base' : 'Business Context'}
                  color="primary"
                  size="small"
                />
              </Box>
            </Paper>

            {/* Alternative: Add files button (optional) */}
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
              <Button
                component="label"
                variant="outlined"
                startIcon={<UploadIcon />}
                size="small"
              >
                Browse Files
                <input
                  type="file"
                  multiple
                  hidden
                  onChange={handleFileSelect}
                  accept=".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls"
                />
              </Button>
            </Box>
          </Box>
        )}

        {/* Selected Files List */}
        {selectedFiles.length > 0 && !isUploading && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Selected Files ({selectedFiles.length})
            </Typography>
            <List>
              {selectedFiles.map((item, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <FileIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={item.file.name}
                    secondary={
                      <>
                        {formatFileSize(item.file.size)} • {item.purpose === 'knowledge_base' ? 'Knowledge Base' : 'Business Context'}
                      </>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton edge="end" onClick={() => handleRemoveFile(index)}>
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Upload Progress */}
        {isUploading && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Uploading Files...
            </Typography>
            <LinearProgress variant="determinate" value={uploadProgress} sx={{ mb: 2 }} />
            <Typography variant="body2" color="textSecondary">
              {Math.round(uploadProgress)}% complete
            </Typography>
          </Box>
        )}

        {/* Upload Results */}
        {uploadResults.length > 0 && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Upload Results
            </Typography>
            <List>
              {uploadResults.map((result) => (
                <ListItem key={result.id}>
                  <ListItemIcon>
                    {result.status === 'success' ? (
                      <SuccessIcon color="success" />
                    ) : (
                      <ErrorIcon color="error" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={result.name}
                    secondary={
                      <>
                        <Typography component="span" variant="caption" color={result.status === 'success' ? 'success.main' : 'error.main'}>
                          {result.message}
                        </Typography>
                        {' • '}
                        <Typography component="span" variant="caption">
                          {result.purpose === 'knowledge_base' ? 'Knowledge Base' : 'Business Context'}
                        </Typography>
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={isUploading}>
          {uploadResults.length > 0 ? 'Close' : 'Cancel'}
        </Button>
        {selectedFiles.length > 0 && !isUploading && uploadResults.length === 0 && (
          <Button
            variant="contained"
            onClick={handleUpload}
            startIcon={<UploadIcon />}
          >
            Upload {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
          </Button>
        )}
        {uploadResults.length > 0 && (
          <Button
            variant="contained"
            component="label"
          >
            Upload More
            <input
              type="file"
              multiple
              hidden
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls"
            />
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};