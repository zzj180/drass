import React, { useRef, useEffect, useState } from 'react';
import {
  Box,
  TextField,
  Paper,
  Typography,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { CharacterCounter } from './CharacterCounter';
import { InputControls } from './InputControls';
import { useTextInput } from './hooks/useTextInput';

export type AttachmentPurpose = 'knowledge_base' | 'business_context';

export interface AttachedFile {
  file: File;
  purpose: AttachmentPurpose;
  id: string;
}

interface InputAreaProps {
  onSend: (message: string) => void;
  onAttach?: () => void;
  onRemoveFile?: (index: number) => void;
  onFilePurposeChange?: (fileId: string, purpose: AttachmentPurpose) => void;
  attachedFiles?: AttachedFile[];
  placeholder?: string;
  maxLength?: number;
  isLoading?: boolean;
  enableAttachment?: boolean;
  enableVoice?: boolean;
  className?: string;
}

/**
 * Main input area component for the chat interface
 * Handles text input, character counting, and send controls
 */
export const InputArea: React.FC<InputAreaProps> = ({
  onSend,
  onAttach,
  onRemoveFile,
  onFilePurposeChange,
  attachedFiles = [],
  placeholder = 'Type your message...',
  maxLength = 4096,
  isLoading = false,
  enableAttachment = true,
  enableVoice = false,
  className,
}) => {
  const textFieldRef = useRef<HTMLTextAreaElement>(null);
  const [purposeDialogOpen, setPurposeDialogOpen] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [selectedPurpose, setSelectedPurpose] = useState<AttachmentPurpose>('business_context');
  
  const {
    value,
    characterCount,
    isMaxLength,
    handleChange,
    handleKeyDown,
    handleSubmit,
    handleFocus,
    handleBlur,
    isFocused,
    canSubmit,
  } = useTextInput({
    maxLength,
    onSubmit: onSend,
    placeholder,
  });

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textFieldRef.current) {
      textFieldRef.current.style.height = 'auto';
      const scrollHeight = textFieldRef.current.scrollHeight;
      // Limit max height to 5 lines (approximately 120px)
      textFieldRef.current.style.height = `${Math.min(scrollHeight, 120)}px`;
    }
  }, [value]);

  // Handle purpose selection
  const handlePurposeChange = (fileId: string) => {
    setSelectedFileId(fileId);
    setPurposeDialogOpen(true);
  };

  const handlePurposeConfirm = () => {
    if (selectedFileId && onFilePurposeChange) {
      onFilePurposeChange(selectedFileId, selectedPurpose);
    }
    setPurposeDialogOpen(false);
    setSelectedFileId(null);
  };

  const handlePurposeCancel = () => {
    setPurposeDialogOpen(false);
    setSelectedFileId(null);
  };

  const getPurposeLabel = (purpose: AttachmentPurpose) => {
    switch (purpose) {
      case 'knowledge_base':
        return '更新知识库';
      case 'business_context':
        return '业务需求配合';
      default:
        return '未知用途';
    }
  };

  const getPurposeColor = (purpose: AttachmentPurpose) => {
    switch (purpose) {
      case 'knowledge_base':
        return 'primary';
      case 'business_context':
        return 'secondary';
      default:
        return 'default';
    }
  };

  return (
    <Paper
      className={className}
      elevation={0}
      sx={{
        p: 2,
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {/* Attached files display */}
        {attachedFiles.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1,
              p: 1,
              bgcolor: 'action.hover',
              borderRadius: 1,
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center', mr: 1 }}>
              Attached files:
            </Typography>
            {attachedFiles.map((attachedFile, index) => (
              <Box key={attachedFile.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={`${attachedFile.file.name} (${(attachedFile.file.size / 1024).toFixed(1)}KB)`}
                  onDelete={onRemoveFile ? () => onRemoveFile(index) : undefined}
                  deleteIcon={<CloseIcon />}
                  size="small"
                  variant="outlined"
                  sx={{
                    maxWidth: '200px',
                    '& .MuiChip-label': {
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    },
                  }}
                />
                <Chip
                  label={getPurposeLabel(attachedFile.purpose)}
                  color={getPurposeColor(attachedFile.purpose) as any}
                  size="small"
                  variant="filled"
                  onClick={() => handlePurposeChange(attachedFile.id)}
                  sx={{ cursor: 'pointer' }}
                />
              </Box>
            ))}
          </Box>
        )}

        {/* Main input container */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: 1,
            p: 1,
            borderRadius: 2,
            border: 1,
            borderColor: isFocused ? 'primary.main' : 'divider',
            bgcolor: 'background.default',
            transition: 'border-color 0.2s',
          }}
        >
          {/* Text input field */}
          <TextField
            inputRef={textFieldRef}
            multiline
            fullWidth
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={isLoading}
            variant="standard"
            InputProps={{
              disableUnderline: true,
              sx: {
                fontSize: '1rem',
                lineHeight: 1.5,
              },
            }}
            sx={{
              '& .MuiInputBase-input': {
                maxHeight: '120px',
                overflowY: 'auto',
                resize: 'none',
                '&::-webkit-scrollbar': {
                  width: '4px',
                },
                '&::-webkit-scrollbar-thumb': {
                  bgcolor: 'action.selected',
                  borderRadius: '2px',
                },
              },
            }}
          />

          {/* Control buttons */}
          <InputControls
            onSend={handleSubmit}
            onAttach={onAttach}
            canSend={canSubmit}
            isLoading={isLoading}
            enableAttachment={enableAttachment}
            enableVoice={enableVoice}
          />
        </Box>

        {/* Footer with character counter and hints */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: 1,
          }}
        >
          {/* Keyboard shortcuts hint */}
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontSize: '0.75rem' }}
          >
            Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line
          </Typography>

          {/* Character counter */}
          {characterCount > 0 && (
            <CharacterCounter
              current={characterCount}
              max={maxLength}
              showProgress={characterCount > maxLength * 0.5}
            />
          )}
        </Box>

        {/* Warning when near limit */}
        {isMaxLength && (
          <Typography
            variant="caption"
            color="error"
            sx={{
              px: 1,
              fontSize: '0.75rem',
            }}
          >
            Maximum character limit reached
          </Typography>
        )}
      </Box>

      {/* Purpose Selection Dialog */}
      <Dialog open={purposeDialogOpen} onClose={handlePurposeCancel} maxWidth="sm" fullWidth>
        <DialogTitle>选择附件用途</DialogTitle>
        <DialogContent>
          <FormControl component="fieldset" sx={{ mt: 2 }}>
            <FormLabel component="legend">请选择此附件的用途：</FormLabel>
            <RadioGroup
              value={selectedPurpose}
              onChange={(e) => setSelectedPurpose(e.target.value as AttachmentPurpose)}
            >
              <FormControlLabel
                value="business_context"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">
                      业务需求配合
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      将附件作为当前对话的上下文，配合生成所需的方案
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="knowledge_base"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">
                      更新知识库
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      将附件内容添加到知识库中，供后续查询使用
                    </Typography>
                  </Box>
                }
              />
            </RadioGroup>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handlePurposeCancel}>取消</Button>
          <Button onClick={handlePurposeConfirm} variant="contained">
            确认
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};