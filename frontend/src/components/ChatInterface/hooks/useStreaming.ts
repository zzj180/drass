import { useState, useCallback, useRef, useEffect } from 'react';

interface UseStreamingOptions {
  onMessage?: (chunk: string) => void;
  onComplete?: (fullContent: string) => void;
  onError?: (error: Error) => void;
  bufferSize?: number;
  throttleMs?: number;
}

interface StreamingState {
  content: string;
  isStreaming: boolean;
  isComplete: boolean;
  error: Error | null;
}

/**
 * Custom hook for handling streaming data with buffering and throttling
 */
export const useStreaming = (options: UseStreamingOptions = {}) => {
  const {
    onMessage,
    onComplete,
    onError,
    bufferSize = 10,
    throttleMs = 50,
  } = options;

  const [state, setState] = useState<StreamingState>({
    content: '',
    isStreaming: false,
    isComplete: false,
    error: null,
  });

  const bufferRef = useRef<string[]>([]);
  const throttleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Flush buffer to state
  const flushBuffer = useCallback(() => {
    if (bufferRef.current.length > 0) {
      const chunk = bufferRef.current.join('');
      bufferRef.current = [];
      
      setState((prev) => ({
        ...prev,
        content: prev.content + chunk,
      }));
      
      onMessage?.(chunk);
    }
  }, [onMessage]);

  // Process incoming chunk with buffering and throttling
  const processChunk = useCallback((chunk: string) => {
    bufferRef.current.push(chunk);
    
    // Flush if buffer is full
    if (bufferRef.current.length >= bufferSize) {
      flushBuffer();
    } else {
      // Schedule throttled flush
      if (throttleTimerRef.current) {
        clearTimeout(throttleTimerRef.current);
      }
      
      throttleTimerRef.current = setTimeout(() => {
        flushBuffer();
      }, throttleMs);
    }
  }, [bufferSize, throttleMs, flushBuffer]);

  // Start streaming
  const startStreaming = useCallback(() => {
    setState({
      content: '',
      isStreaming: true,
      isComplete: false,
      error: null,
    });
    
    abortControllerRef.current = new AbortController();
  }, []);

  // Append chunk to stream
  const appendChunk = useCallback((chunk: string) => {
    if (!state.isStreaming) {
      console.warn('Attempted to append chunk when not streaming');
      return;
    }
    
    processChunk(chunk);
  }, [state.isStreaming, processChunk]);

  // Complete streaming
  const completeStreaming = useCallback(() => {
    // Flush any remaining buffer
    flushBuffer();
    
    // Clear throttle timer
    if (throttleTimerRef.current) {
      clearTimeout(throttleTimerRef.current);
      throttleTimerRef.current = null;
    }
    
    setState((prev) => {
      onComplete?.(prev.content);
      
      return {
        ...prev,
        isStreaming: false,
        isComplete: true,
      };
    });
  }, [flushBuffer, onComplete]);

  // Handle streaming error
  const handleError = useCallback((error: Error) => {
    // Clear any pending operations
    if (throttleTimerRef.current) {
      clearTimeout(throttleTimerRef.current);
      throttleTimerRef.current = null;
    }
    
    bufferRef.current = [];
    
    setState((prev) => ({
      ...prev,
      isStreaming: false,
      isComplete: false,
      error,
    }));
    
    onError?.(error);
  }, [onError]);

  // Abort streaming
  const abortStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    completeStreaming();
  }, [completeStreaming]);

  // Reset state
  const reset = useCallback(() => {
    setState({
      content: '',
      isStreaming: false,
      isComplete: false,
      error: null,
    });
    
    bufferRef.current = [];
    
    if (throttleTimerRef.current) {
      clearTimeout(throttleTimerRef.current);
      throttleTimerRef.current = null;
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  // Stream from async generator
  const streamFromGenerator = useCallback(
    async function* (generator: AsyncGenerator<string>) {
      startStreaming();
      
      try {
        for await (const chunk of generator) {
          if (abortControllerRef.current?.signal.aborted) {
            break;
          }
          
          appendChunk(chunk);
          yield chunk;
        }
        
        completeStreaming();
      } catch (error) {
        handleError(error as Error);
        throw error;
      }
    },
    [startStreaming, appendChunk, completeStreaming, handleError]
  );

  // Stream from fetch response
  const streamFromResponse = useCallback(
    async (response: Response) => {
      if (!response.body) {
        throw new Error('Response body is null');
      }
      
      startStreaming();
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      try {
        let done = false;
        while (!done) {
          const result = await reader.read();
          done = result.done;
          
          if (done || abortControllerRef.current?.signal.aborted) {
            break;
          }
          
          const chunk = decoder.decode(result.value, { stream: true });
          appendChunk(chunk);
        }
        
        completeStreaming();
      } catch (error) {
        handleError(error as Error);
      } finally {
        reader.releaseLock();
      }
    },
    [startStreaming, appendChunk, completeStreaming, handleError]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (throttleTimerRef.current) {
        clearTimeout(throttleTimerRef.current);
      }
      
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    // State
    content: state.content,
    isStreaming: state.isStreaming,
    isComplete: state.isComplete,
    error: state.error,
    
    // Actions
    startStreaming,
    appendChunk,
    completeStreaming,
    abortStreaming,
    handleError,
    reset,
    
    // Utilities
    streamFromGenerator,
    streamFromResponse,
  };
};