import React, { useEffect, useRef, useCallback } from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Fade,
} from '@mui/material';
import { MessageItem } from './MessageItem';
import { LoadingIndicator } from './LoadingIndicator';
import { StreamingMessage } from './StreamingMessage';
import { MessageListProps } from './types';

/**
 * MessageList component displays a scrollable list of messages
 * with automatic scrolling to bottom and virtual scrolling for performance
 */
export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  onMessageAction,
  className,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastMessageCountRef = useRef(messages.length);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback((smooth = true) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: smooth ? 'smooth' : 'auto',
        block: 'end',
      });
    }
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    // Only scroll if a new message was added (not on edits)
    if (messages.length > lastMessageCountRef.current) {
      scrollToBottom();
    }
    lastMessageCountRef.current = messages.length;
  }, [messages.length, scrollToBottom]);

  // Initial scroll to bottom
  useEffect(() => {
    scrollToBottom(false);
  }, [scrollToBottom]);

  const handleMessageAction = useCallback(
    (action: string, messageId: string) => {
      onMessageAction?.(action, messageId);
    },
    [onMessageAction]
  );

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return (
      <Box
        className={className}
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 4,
        }}
      >
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ textAlign: 'center' }}
        >
          No messages yet. Start a conversation!
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      ref={scrollContainerRef}
      className={className}
      sx={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        p: 2,
        // Custom scrollbar styling
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          bgcolor: 'action.hover',
          borderRadius: '4px',
        },
        '&::-webkit-scrollbar-thumb': {
          bgcolor: 'action.selected',
          borderRadius: '4px',
          '&:hover': {
            bgcolor: 'action.disabled',
          },
        },
      }}
    >
      {/* Messages */}
      {messages.map((message, index) => (
        <Fade in key={message.id} timeout={300}>
          <Box>
            {message.isStreaming ? (
              <StreamingMessage
                content={message.content}
                isStreaming={true}
                isComplete={false}
              />
            ) : (
              <MessageItem
                message={message}
                onAction={(action) =>
                  handleMessageAction(action, message.id)
                }
                showActions={true}
              />
            )}
          </Box>
        </Fade>
      ))}

      {/* Loading indicator */}
      {isLoading && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'flex-start',
            ml: 6,
          }}
        >
          <LoadingIndicator 
            type="dots" 
            size="small" 
            text="Assistant is typing..." 
          />
        </Box>
      )}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} style={{ height: 1 }} />
    </Box>
  );
};

// Performance optimization: Memoize component to prevent unnecessary re-renders
export default React.memo(MessageList);