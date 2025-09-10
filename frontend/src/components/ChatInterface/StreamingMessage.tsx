import React, { useEffect, useState } from 'react';
import { Box, Fade } from '@mui/material';
import { MarkdownRenderer } from './MarkdownRenderer';
import { LoadingIndicator } from './LoadingIndicator';

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
  isComplete: boolean;
  className?: string;
}

/**
 * Component for displaying streaming messages with real-time updates
 * Shows content as it arrives and indicates streaming status
 */
export const StreamingMessage: React.FC<StreamingMessageProps> = ({
  content,
  isStreaming,
  isComplete,
  className,
}) => {
  const [displayContent, setDisplayContent] = useState('');
  const [showCursor, setShowCursor] = useState(true);

  // Update display content when new content arrives
  useEffect(() => {
    setDisplayContent(content);
  }, [content]);

  // Blinking cursor effect while streaming
  useEffect(() => {
    if (!isStreaming) {
      setShowCursor(false);
      return;
    }

    const interval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 500);

    return () => clearInterval(interval);
  }, [isStreaming]);

  return (
    <Box className={className} sx={{ position: 'relative' }}>
      {/* Main content with markdown rendering */}
      <MarkdownRenderer content={displayContent} />
      
      {/* Streaming cursor indicator */}
      {isStreaming && (
        <Fade in={showCursor} timeout={200}>
          <Box
            component="span"
            sx={{
              display: 'inline-block',
              width: '2px',
              height: '1em',
              bgcolor: 'primary.main',
              ml: 0.5,
              animation: 'blink 1s infinite',
              '@keyframes blink': {
                '0%': { opacity: 1 },
                '50%': { opacity: 0 },
                '100%': { opacity: 1 },
              },
            }}
          />
        </Fade>
      )}
      
      {/* Loading indicator for initial response */}
      {!content && isStreaming && (
        <LoadingIndicator size="small" text="Thinking..." />
      )}
      
      {/* Completion indicator */}
      {isComplete && !isStreaming && content && (
        <Fade in timeout={500}>
          <Box
            sx={{
              display: 'inline-block',
              width: 6,
              height: 6,
              borderRadius: '50%',
              bgcolor: 'success.main',
              ml: 1,
              verticalAlign: 'middle',
            }}
          />
        </Fade>
      )}
    </Box>
  );
};

export default StreamingMessage;