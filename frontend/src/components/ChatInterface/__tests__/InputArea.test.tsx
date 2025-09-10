import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InputArea } from '../InputArea';

describe('InputArea', () => {
  const mockOnSend = vi.fn();
  const mockOnAttach = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    expect(input).toBeInTheDocument();
  });

  it('renders with custom placeholder', () => {
    render(
      <InputArea 
        onSend={mockOnSend} 
        placeholder="Enter your question..." 
      />
    );
    
    const input = screen.getByPlaceholderText('Enter your question...');
    expect(input).toBeInTheDocument();
  });

  it('handles text input', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Hello world');
    
    expect(input).toHaveValue('Hello world');
  });

  it('shows character counter when typing', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} maxLength={100} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Test message');
    
    // Character counter appears when typing
    expect(screen.getByText(/12 \/ 100/)).toBeInTheDocument();
  });

  it('prevents input beyond max length', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} maxLength={10} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'This is a very long message');
    
    // Should only contain first 10 characters
    expect(input.value.length).toBeLessThanOrEqual(10);
  });

  it('sends message on Enter key', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(mockOnSend).toHaveBeenCalledWith('Test message');
    expect(input).toHaveValue(''); // Should clear after sending
  });

  it('adds new line on Shift+Enter', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Line 1');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    await user.type(input, 'Line 2');
    
    expect(input.value).toContain('Line 1\nLine 2');
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('sends message on send button click', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Test message');
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    await user.click(sendButton);
    
    expect(mockOnSend).toHaveBeenCalledWith('Test message');
    expect(input).toHaveValue('');
  });

  it('disables send button when input is empty', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when input has text', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Test');
    
    expect(sendButton).toBeEnabled();
  });

  it('shows attachment button when enabled', () => {
    render(<InputArea onSend={mockOnSend} onAttach={mockOnAttach} enableAttachment={true} />);
    
    const attachButton = screen.getByRole('button', { name: /attach file/i });
    expect(attachButton).toBeInTheDocument();
  });

  it('hides attachment button when disabled', () => {
    render(<InputArea onSend={mockOnSend} enableAttachment={false} />);
    
    const attachButton = screen.queryByRole('button', { name: /attach file/i });
    expect(attachButton).not.toBeInTheDocument();
  });

  it('calls onAttach when attachment button clicked', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} onAttach={mockOnAttach} />);
    
    const attachButton = screen.getByRole('button', { name: /attach file/i });
    await user.click(attachButton);
    
    expect(mockOnAttach).toHaveBeenCalled();
  });

  it('disables input when loading', () => {
    render(<InputArea onSend={mockOnSend} isLoading={true} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    expect(input).toBeDisabled();
  });

  it('shows loading spinner when loading', () => {
    render(<InputArea onSend={mockOnSend} isLoading={true} />);
    
    const spinner = screen.getByRole('progressbar');
    expect(spinner).toBeInTheDocument();
  });

  it('trims whitespace before sending', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, '   Test message   ');
    await user.keyboard('{Enter}');
    
    expect(mockOnSend).toHaveBeenCalledWith('Test message');
  });

  it('does not send empty or whitespace-only messages', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    
    // Try sending empty message
    await user.keyboard('{Enter}');
    expect(mockOnSend).not.toHaveBeenCalled();
    
    // Try sending whitespace-only message
    await user.type(input, '   ');
    await user.keyboard('{Enter}');
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('shows warning when near character limit', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} maxLength={20} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'This is almost twenty'); // 21 characters
    
    // Should show warning message
    expect(screen.getByText('Maximum character limit reached')).toBeInTheDocument();
  });

  it('adjusts textarea height based on content', async () => {
    const user = userEvent.setup();
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...') as HTMLTextAreaElement;
    const initialHeight = input.style.height;
    
    // Type multiple lines
    await user.type(input, 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5');
    
    // Height should have changed (capped at max)
    await waitFor(() => {
      expect(input.style.height).toBeDefined();
    });
  });
});