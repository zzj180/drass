import React from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  Mic as MicIcon,
  Stop as StopIcon,
} from '@mui/icons-material';

interface InputControlsProps {
  onSend: () => void;
  onAttach?: () => void;
  onVoice?: () => void;
  onStop?: () => void;
  canSend: boolean;
  isLoading?: boolean;
  isRecording?: boolean;
  enableAttachment?: boolean;
  enableVoice?: boolean;
  className?: string;
}

/**
 * Input control buttons for the chat interface
 */
export const InputControls: React.FC<InputControlsProps> = ({
  onSend,
  onAttach,
  onVoice,
  onStop,
  canSend,
  isLoading = false,
  isRecording = false,
  enableAttachment = true,
  enableVoice = false,
  className,
}) => {
  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        gap: 1,
        alignItems: 'center',
      }}
    >
      {/* Attachment button */}
      {enableAttachment && onAttach && (
        <Tooltip title="Attach file">
          <IconButton
            onClick={onAttach}
            disabled={isLoading}
            size="medium"
            sx={{
              color: 'action.active',
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <AttachFileIcon />
          </IconButton>
        </Tooltip>
      )}

      {/* Voice input button */}
      {enableVoice && onVoice && (
        <Tooltip title={isRecording ? "Stop recording" : "Voice input"}>
          <IconButton
            onClick={isRecording ? onStop : onVoice}
            disabled={isLoading}
            size="medium"
            sx={{
              color: isRecording ? 'error.main' : 'action.active',
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            {isRecording ? <StopIcon /> : <MicIcon />}
          </IconButton>
        </Tooltip>
      )}

      {/* Send button */}
      <Tooltip title="Send message (Enter)">
        <span>
          <IconButton
            onClick={onSend}
            disabled={!canSend || isLoading}
            size="medium"
            color="primary"
            sx={{
              bgcolor: canSend && !isLoading ? 'primary.main' : 'action.disabledBackground',
              color: canSend && !isLoading ? 'primary.contrastText' : 'action.disabled',
              '&:hover': {
                bgcolor: canSend && !isLoading ? 'primary.dark' : 'action.disabledBackground',
              },
              '&:disabled': {
                color: 'action.disabled',
              },
            }}
          >
            {isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              <SendIcon />
            )}
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
};