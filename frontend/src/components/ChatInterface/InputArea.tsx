import React, { useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  Paper,
  Typography,
} from '@mui/material';
import { CharacterCounter } from './CharacterCounter';
import { InputControls } from './InputControls';
import { useTextInput } from './hooks/useTextInput';

interface InputAreaProps {
  onSend: (message: string) => void;
  onAttach?: () => void;
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
  placeholder = 'Type your message...',
  maxLength = 4096,
  isLoading = false,
  enableAttachment = true,
  enableVoice = false,
  className,
}) => {
  const textFieldRef = useRef<HTMLTextAreaElement>(null);
  
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
    </Paper>
  );
};