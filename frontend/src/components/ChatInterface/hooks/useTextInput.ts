import { useState, useCallback, KeyboardEvent, ChangeEvent } from 'react';

interface UseTextInputOptions {
  maxLength?: number;
  onSubmit?: (text: string) => void;
  placeholder?: string;
}

/**
 * Custom hook for managing text input state and behavior
 */
export const useTextInput = (options: UseTextInputOptions = {}) => {
  const { maxLength = 4096, onSubmit } = options;
  
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  
  // Calculate character count
  const characterCount = value.length;
  const isMaxLength = characterCount >= maxLength;
  const characterPercentage = (characterCount / maxLength) * 100;
  
  // Handle text change
  const handleChange = useCallback(
    (event: ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = event.target.value;
      if (newValue.length <= maxLength) {
        setValue(newValue);
      }
    },
    [maxLength]
  );
  
  // Handle key press for Enter/Shift+Enter
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      // Enter without Shift submits
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        
        const trimmedValue = value.trim();
        if (trimmedValue) {
          onSubmit?.(trimmedValue);
          setValue(''); // Clear after submit
        }
      }
      // Shift+Enter adds new line (default behavior)
    },
    [value, onSubmit]
  );
  
  // Handle submit button click
  const handleSubmit = useCallback(() => {
    const trimmedValue = value.trim();
    if (trimmedValue) {
      onSubmit?.(trimmedValue);
      setValue(''); // Clear after submit
    }
  }, [value, onSubmit]);
  
  // Clear input
  const clear = useCallback(() => {
    setValue('');
  }, []);
  
  // Set focus state
  const handleFocus = useCallback(() => {
    setIsFocused(true);
  }, []);
  
  const handleBlur = useCallback(() => {
    setIsFocused(false);
  }, []);
  
  return {
    value,
    setValue,
    isFocused,
    characterCount,
    characterPercentage,
    isMaxLength,
    handleChange,
    handleKeyDown,
    handleSubmit,
    handleFocus,
    handleBlur,
    clear,
    canSubmit: value.trim().length > 0,
  };
};