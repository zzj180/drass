import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { StreamingMessage } from '../StreamingMessage';

// Mock the dependencies
vi.mock('../MarkdownRenderer', () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div>{content}</div>,
}));

vi.mock('../LoadingIndicator', () => ({
  LoadingIndicator: ({ text }: { text: string }) => <div>{text}</div>,
}));

describe('StreamingMessage', () => {
  it('renders content when provided', () => {
    render(
      <StreamingMessage 
        content="Hello world" 
        isStreaming={false} 
        isComplete={true} 
      />
    );
    
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('shows loading indicator when streaming without content', () => {
    render(
      <StreamingMessage 
        content="" 
        isStreaming={true} 
        isComplete={false} 
      />
    );
    
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('shows cursor when streaming', async () => {
    const { container } = render(
      <StreamingMessage 
        content="Streaming content" 
        isStreaming={true} 
        isComplete={false} 
      />
    );
    
    // Look for the cursor element
    await waitFor(() => {
      const cursor = container.querySelector('[style*="animation"]');
      expect(cursor).toBeInTheDocument();
    });
  });

  it('hides cursor when not streaming', () => {
    const { container } = render(
      <StreamingMessage 
        content="Static content" 
        isStreaming={false} 
        isComplete={true} 
      />
    );
    
    const cursor = container.querySelector('[style*="animation"]');
    expect(cursor).not.toBeInTheDocument();
  });

  it('shows completion indicator when complete', async () => {
    const { container } = render(
      <StreamingMessage 
        content="Complete message" 
        isStreaming={false} 
        isComplete={true} 
      />
    );
    
    // Look for the green dot completion indicator
    await waitFor(() => {
      const indicator = container.querySelector('[style*="border-radius: 50%"]');
      expect(indicator).toBeInTheDocument();
    });
  });

  it('updates content dynamically', () => {
    const { rerender } = render(
      <StreamingMessage 
        content="Initial" 
        isStreaming={true} 
        isComplete={false} 
      />
    );
    
    expect(screen.getByText('Initial')).toBeInTheDocument();
    
    rerender(
      <StreamingMessage 
        content="Initial content updated" 
        isStreaming={true} 
        isComplete={false} 
      />
    );
    
    expect(screen.getByText('Initial content updated')).toBeInTheDocument();
  });

  it('transitions from streaming to complete', async () => {
    const { rerender, container } = render(
      <StreamingMessage 
        content="Message" 
        isStreaming={true} 
        isComplete={false} 
      />
    );
    
    // Should show cursor while streaming
    await waitFor(() => {
      const cursor = container.querySelector('[style*="animation"]');
      expect(cursor).toBeInTheDocument();
    });
    
    rerender(
      <StreamingMessage 
        content="Message complete" 
        isStreaming={false} 
        isComplete={true} 
      />
    );
    
    // Should show completion indicator
    await waitFor(() => {
      const indicator = container.querySelector('[style*="border-radius: 50%"]');
      expect(indicator).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const { container } = render(
      <StreamingMessage 
        content="Test" 
        isStreaming={false} 
        isComplete={true} 
        className="custom-class" 
      />
    );
    
    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });
});