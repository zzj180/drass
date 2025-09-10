import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MessageItem } from '../MessageItem';
import { Message } from '../types';

describe('MessageItem', () => {
  const mockMessage: Message = {
    id: '1',
    role: 'user',
    content: 'Test message content',
    timestamp: new Date('2024-01-01T10:00:00'),
    status: 'sent',
  };

  const mockOnAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render message content correctly', () => {
    render(<MessageItem message={mockMessage} />);
    
    expect(screen.getByText('Test message content')).toBeInTheDocument();
  });

  it('should display user messages on the right', () => {
    const { container } = render(<MessageItem message={mockMessage} />);
    const messageBox = container.firstChild as HTMLElement;
    
    expect(messageBox).toHaveStyle({ justifyContent: 'flex-end' });
  });

  it('should display assistant messages on the left', () => {
    const assistantMessage = { ...mockMessage, role: 'assistant' as const };
    const { container } = render(<MessageItem message={assistantMessage} />);
    const messageBox = container.firstChild as HTMLElement;
    
    expect(messageBox).toHaveStyle({ justifyContent: 'flex-start' });
  });

  it('should show timestamp', () => {
    render(<MessageItem message={mockMessage} />);
    
    // Check if timestamp is rendered (format will vary)
    expect(screen.getByText(/ago/)).toBeInTheDocument();
  });

  it('should handle copy action', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    render(
      <MessageItem 
        message={mockMessage} 
        onAction={mockOnAction}
        showActions={true}
      />
    );

    // Hover to show actions
    const messageElement = screen.getByText('Test message content').closest('div');
    fireEvent.mouseEnter(messageElement!);

    // Click copy button
    const copyButton = screen.getByLabelText('Copy');
    fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test message content');
    expect(mockOnAction).toHaveBeenCalledWith('copy');
  });

  it('should show edit button for user messages', () => {
    render(
      <MessageItem 
        message={mockMessage} 
        onAction={mockOnAction}
        showActions={true}
      />
    );

    const messageElement = screen.getByText('Test message content').closest('div');
    fireEvent.mouseEnter(messageElement!);

    expect(screen.getByLabelText('Edit')).toBeInTheDocument();
  });

  it('should show regenerate button for assistant messages', () => {
    const assistantMessage = { ...mockMessage, role: 'assistant' as const };
    
    render(
      <MessageItem 
        message={assistantMessage} 
        onAction={mockOnAction}
        showActions={true}
      />
    );

    const messageElement = screen.getByText('Test message content').closest('div');
    fireEvent.mouseEnter(messageElement!);

    expect(screen.getByLabelText('Regenerate')).toBeInTheDocument();
  });

  it('should display error state', () => {
    const errorMessage = {
      ...mockMessage,
      status: 'error' as const,
      error: 'Network error',
    };

    render(<MessageItem message={errorMessage} />);
    
    expect(screen.getByText('Error: Network error')).toBeInTheDocument();
  });

  it('should not show actions when showActions is false', () => {
    render(
      <MessageItem 
        message={mockMessage} 
        showActions={false}
      />
    );

    const messageElement = screen.getByText('Test message content').closest('div');
    fireEvent.mouseEnter(messageElement!);

    expect(screen.queryByLabelText('Copy')).not.toBeInTheDocument();
  });
});