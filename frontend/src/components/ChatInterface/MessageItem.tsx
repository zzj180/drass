import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as AssistantIcon,
  Info as SystemIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { MessageItemProps, MessageRole } from './types';

/**
 * MessageItem component displays a single message in the chat
 */
export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onAction,
  showActions = true,
  className,
}) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const getAvatar = (role: MessageRole) => {
    switch (role) {
      case 'user':
        return <PersonIcon />;
      case 'assistant':
        return <AssistantIcon />;
      case 'system':
        return <SystemIcon />;
    }
  };

  const getAvatarColor = (role: MessageRole) => {
    switch (role) {
      case 'user':
        return 'primary.main';
      case 'assistant':
        return 'secondary.main';
      case 'system':
        return 'grey.500';
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    onAction?.('copy');
  };

  const handleEdit = () => {
    onAction?.('edit');
  };

  const handleRegenerate = () => {
    onAction?.('regenerate');
  };

  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
        px: 2,
      }}
    >
      {!isUser && (
        <Avatar
          sx={{
            bgcolor: getAvatarColor(message.role),
            mr: 1,
            width: 36,
            height: 36,
          }}
        >
          {getAvatar(message.role)}
        </Avatar>
      )}

      <Paper
        elevation={1}
        sx={{
          maxWidth: '70%',
          minWidth: '200px',
          p: 2,
          bgcolor: isUser
            ? 'primary.light'
            : isSystem
            ? 'grey.100'
            : 'background.paper',
          color: isUser ? 'primary.contrastText' : 'text.primary',
          borderRadius: 2,
          position: 'relative',
          '&:hover .message-actions': {
            opacity: 1,
          },
        }}
      >
        {/* Message content */}
        <Typography
          variant="body1"
          sx={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {message.content}
        </Typography>

        {/* Timestamp */}
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 1,
            opacity: 0.7,
            fontSize: '0.75rem',
          }}
        >
          {formatDistanceToNow(message.timestamp, { addSuffix: true })}
        </Typography>

        {/* Message actions */}
        {showActions && !isSystem && (
          <Box
            className="message-actions"
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              display: 'flex',
              gap: 0.5,
              opacity: 0,
              transition: 'opacity 0.2s',
              bgcolor: 'background.paper',
              borderRadius: 1,
              boxShadow: 1,
            }}
          >
            <Tooltip title="Copy">
              <IconButton size="small" onClick={handleCopy}>
                <CopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>

            {isUser && (
              <Tooltip title="Edit">
                <IconButton size="small" onClick={handleEdit}>
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}

            {!isUser && (
              <Tooltip title="Regenerate">
                <IconButton size="small" onClick={handleRegenerate}>
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        )}

        {/* Error state */}
        {message.status === 'error' && (
          <Typography
            variant="caption"
            color="error"
            sx={{ display: 'block', mt: 1 }}
          >
            Error: {message.error || 'Failed to send message'}
          </Typography>
        )}
      </Paper>

      {isUser && (
        <Avatar
          sx={{
            bgcolor: getAvatarColor(message.role),
            ml: 1,
            width: 36,
            height: 36,
          }}
        >
          {getAvatar(message.role)}
        </Avatar>
      )}
    </Box>
  );
};