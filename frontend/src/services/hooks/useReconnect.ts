import { useEffect, useRef, useState, useCallback } from 'react';

interface UseReconnectOptions {
  maxAttempts?: number;
  interval?: number;
  backoff?: boolean;
  backoffMultiplier?: number;
  maxInterval?: number;
  onReconnect?: () => void;
  onMaxAttemptsReached?: () => void;
}

interface UseReconnectReturn {
  isReconnecting: boolean;
  attempts: number;
  nextAttemptIn: number | null;
  startReconnect: () => void;
  stopReconnect: () => void;
  reset: () => void;
}

/**
 * Custom hook for managing reconnection logic
 */
export const useReconnect = (
  reconnectFn: () => Promise<boolean>,
  options: UseReconnectOptions = {}
): UseReconnectReturn => {
  const {
    maxAttempts = 5,
    interval = 3000,
    backoff = true,
    backoffMultiplier = 1.5,
    maxInterval = 30000,
    onReconnect,
    onMaxAttemptsReached,
  } = options;

  const [isReconnecting, setIsReconnecting] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [nextAttemptIn, setNextAttemptIn] = useState<number | null>(null);
  
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(false);
  const attemptCountRef = useRef(0);

  // Calculate delay for next attempt
  const calculateDelay = useCallback(
    (attemptNumber: number): number => {
      if (!backoff) {
        return interval;
      }
      
      const delay = interval * Math.pow(backoffMultiplier, attemptNumber - 1);
      return Math.min(delay, maxInterval);
    },
    [interval, backoff, backoffMultiplier, maxInterval]
  );

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
    
    setNextAttemptIn(null);
  }, []);

  // Perform reconnection attempt
  const attemptReconnect = useCallback(async () => {
    if (!shouldReconnectRef.current) {
      return;
    }

    attemptCountRef.current++;
    setAttempts(attemptCountRef.current);
    
    console.log(`[useReconnect] Attempt ${attemptCountRef.current}/${maxAttempts}`);
    
    try {
      const success = await reconnectFn();
      
      if (success) {
        console.log('[useReconnect] Reconnection successful');
        onReconnect?.();
        setIsReconnecting(false);
        shouldReconnectRef.current = false;
        attemptCountRef.current = 0;
        setAttempts(0);
        clearTimers();
      } else if (attemptCountRef.current < maxAttempts && shouldReconnectRef.current) {
        // Schedule next attempt
        const delay = calculateDelay(attemptCountRef.current);
        console.log(`[useReconnect] Next attempt in ${delay}ms`);
        
        // Start countdown
        setNextAttemptIn(Math.ceil(delay / 1000));
        let remaining = delay;
        
        countdownTimerRef.current = setInterval(() => {
          remaining -= 1000;
          if (remaining <= 0) {
            if (countdownTimerRef.current) {
              clearInterval(countdownTimerRef.current);
              countdownTimerRef.current = null;
            }
            setNextAttemptIn(null);
          } else {
            setNextAttemptIn(Math.ceil(remaining / 1000));
          }
        }, 1000);
        
        reconnectTimerRef.current = setTimeout(() => {
          reconnectTimerRef.current = null;
          attemptReconnect();
        }, delay);
      } else {
        // Max attempts reached
        console.log('[useReconnect] Max attempts reached');
        onMaxAttemptsReached?.();
        setIsReconnecting(false);
        shouldReconnectRef.current = false;
        clearTimers();
      }
    } catch (error) {
      console.error('[useReconnect] Reconnection error:', error);
      
      if (attemptCountRef.current < maxAttempts && shouldReconnectRef.current) {
        // Schedule next attempt after error
        const delay = calculateDelay(attemptCountRef.current);
        
        setNextAttemptIn(Math.ceil(delay / 1000));
        let remaining = delay;
        
        countdownTimerRef.current = setInterval(() => {
          remaining -= 1000;
          if (remaining <= 0) {
            if (countdownTimerRef.current) {
              clearInterval(countdownTimerRef.current);
              countdownTimerRef.current = null;
            }
            setNextAttemptIn(null);
          } else {
            setNextAttemptIn(Math.ceil(remaining / 1000));
          }
        }, 1000);
        
        reconnectTimerRef.current = setTimeout(() => {
          reconnectTimerRef.current = null;
          attemptReconnect();
        }, delay);
      } else {
        onMaxAttemptsReached?.();
        setIsReconnecting(false);
        shouldReconnectRef.current = false;
        clearTimers();
      }
    }
  }, [reconnectFn, maxAttempts, calculateDelay, onReconnect, onMaxAttemptsReached, clearTimers]);

  // Start reconnection process
  const startReconnect = useCallback(() => {
    if (isReconnecting || shouldReconnectRef.current) {
      console.log('[useReconnect] Already reconnecting');
      return;
    }
    
    console.log('[useReconnect] Starting reconnection process');
    shouldReconnectRef.current = true;
    attemptCountRef.current = 0;
    setAttempts(0);
    setIsReconnecting(true);
    attemptReconnect();
  }, [isReconnecting, attemptReconnect]);

  // Stop reconnection process
  const stopReconnect = useCallback(() => {
    console.log('[useReconnect] Stopping reconnection process');
    shouldReconnectRef.current = false;
    setIsReconnecting(false);
    clearTimers();
  }, [clearTimers]);

  // Reset state
  const reset = useCallback(() => {
    stopReconnect();
    attemptCountRef.current = 0;
    setAttempts(0);
  }, [stopReconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false;
      clearTimers();
    };
  }, [clearTimers]);

  return {
    isReconnecting,
    attempts,
    nextAttemptIn,
    startReconnect,
    stopReconnect,
    reset,
  };
};

export default useReconnect;