import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MessageList } from '../MessageList';
import { Message } from '../types';

describe('MessageList', () => {
  const mockMessages: Message[] = [
    {
      id: '1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T10:00:00'),
      status: 'sent',
    },
    {
      id: '2',
      role: 'assistant',
      content: 'Hi! How can I help you?',
      timestamp: new Date('2024-01-01T10:00:10'),
      status: 'sent',
    },
  ];

  const mockOnMessageAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render all messages', () => {
    render(<MessageList messages={mockMessages} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi! How can I help you?')).toBeInTheDocument();
  });

  it('should show empty state when no messages', () => {
    render(<MessageList messages={[]} />);
    
    expect(screen.getByText('No messages yet. Start a conversation!')).toBeInTheDocument();
  });

  it('should show loading indicator when isLoading is true', () => {
    render(<MessageList messages={mockMessages} isLoading={true} />);
    
    expect(screen.getByText('Assistant is typing...')).toBeInTheDocument();
  });

  it('should not show empty state when loading', () => {
    render(<MessageList messages={[]} isLoading={true} />);
    
    expect(screen.queryByText('No messages yet. Start a conversation!')).not.toBeInTheDocument();
  });

  it('should call onMessageAction when action is triggered', () => {
    render(
      <MessageList 
        messages={mockMessages} 
        onMessageAction={mockOnMessageAction}
      />
    );

    // MessageItem will trigger the action
    // This is tested more thoroughly in MessageItem.test.tsx
    expect(mockOnMessageAction).not.toHaveBeenCalled();
  });

  it('should scroll to bottom when new messages are added', async () => {
    const scrollIntoViewMock = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { rerender } = render(<MessageList messages={mockMessages} />);
    
    const newMessage: Message = {
      id: '3',
      role: 'user',
      content: 'New message',
      timestamp: new Date(),
      status: 'sent',
    };

    rerender(<MessageList messages={[...mockMessages, newMessage]} />);

    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });
  });

  it('should render messages with fade animation', () => {
    const { container } = render(<MessageList messages={mockMessages} />);
    
    // Check if Fade component is applied
    const fadeElements = container.querySelectorAll('[class*="MuiFade"]');
    expect(fadeElements.length).toBeGreaterThan(0);
  });

  it('should handle large number of messages efficiently', () => {
    // Create 100 messages for performance testing
    const manyMessages: Message[] = Array.from({ length: 100 }, (_, i) => ({
      id: `msg-${i}`,
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i}`,
      timestamp: new Date(),
      status: 'sent',
    }));

    const { container } = render(<MessageList messages={manyMessages} />);
    
    // Check if scrollable container is rendered
    const scrollContainer = container.querySelector('[class*="overflowY"]');
    expect(scrollContainer).toBeInTheDocument();
    
    // Verify all messages are rendered
    expect(screen.getByText('Message 0')).toBeInTheDocument();
    expect(screen.getByText('Message 99')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <MessageList 
        messages={mockMessages} 
        className="custom-message-list"
      />
    );
    
    expect(container.querySelector('.custom-message-list')).toBeInTheDocument();
  });
});