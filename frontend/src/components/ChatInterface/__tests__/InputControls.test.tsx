import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InputControls } from '../InputControls';

describe('InputControls', () => {
  const mockOnSend = vi.fn();
  const mockOnAttach = vi.fn();
  const mockOnVoice = vi.fn();
  const mockOnStop = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders send button', () => {
    render(<InputControls onSend={mockOnSend} canSend={true} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeInTheDocument();
  });

  it('disables send button when canSend is false', () => {
    render(<InputControls onSend={mockOnSend} canSend={false} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when canSend is true', () => {
    render(<InputControls onSend={mockOnSend} canSend={true} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeEnabled();
  });

  it('calls onSend when send button clicked', async () => {
    const user = userEvent.setup();
    render(<InputControls onSend={mockOnSend} canSend={true} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    await user.click(sendButton);
    
    expect(mockOnSend).toHaveBeenCalled();
  });

  it('shows attachment button when enabled', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        onAttach={mockOnAttach}
        canSend={true}
        enableAttachment={true}
      />
    );
    
    const attachButton = screen.getByRole('button', { name: /attach file/i });
    expect(attachButton).toBeInTheDocument();
  });

  it('hides attachment button when disabled', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        canSend={true}
        enableAttachment={false}
      />
    );
    
    const attachButton = screen.queryByRole('button', { name: /attach file/i });
    expect(attachButton).not.toBeInTheDocument();
  });

  it('calls onAttach when attachment button clicked', async () => {
    const user = userEvent.setup();
    render(
      <InputControls 
        onSend={mockOnSend} 
        onAttach={mockOnAttach}
        canSend={true}
        enableAttachment={true}
      />
    );
    
    const attachButton = screen.getByRole('button', { name: /attach file/i });
    await user.click(attachButton);
    
    expect(mockOnAttach).toHaveBeenCalled();
  });

  it('shows voice button when enabled', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        onVoice={mockOnVoice}
        canSend={true}
        enableVoice={true}
      />
    );
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    expect(voiceButton).toBeInTheDocument();
  });

  it('hides voice button when disabled', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        canSend={true}
        enableVoice={false}
      />
    );
    
    const voiceButton = screen.queryByRole('button', { name: /voice input/i });
    expect(voiceButton).not.toBeInTheDocument();
  });

  it('shows stop button when recording', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        onVoice={mockOnVoice}
        onStop={mockOnStop}
        canSend={true}
        enableVoice={true}
        isRecording={true}
      />
    );
    
    const stopButton = screen.getByRole('button', { name: /stop recording/i });
    expect(stopButton).toBeInTheDocument();
  });

  it('calls onVoice when voice button clicked', async () => {
    const user = userEvent.setup();
    render(
      <InputControls 
        onSend={mockOnSend} 
        onVoice={mockOnVoice}
        canSend={true}
        enableVoice={true}
        isRecording={false}
      />
    );
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    await user.click(voiceButton);
    
    expect(mockOnVoice).toHaveBeenCalled();
  });

  it('calls onStop when stop button clicked while recording', async () => {
    const user = userEvent.setup();
    render(
      <InputControls 
        onSend={mockOnSend} 
        onVoice={mockOnVoice}
        onStop={mockOnStop}
        canSend={true}
        enableVoice={true}
        isRecording={true}
      />
    );
    
    const stopButton = screen.getByRole('button', { name: /stop recording/i });
    await user.click(stopButton);
    
    expect(mockOnStop).toHaveBeenCalled();
    expect(mockOnVoice).not.toHaveBeenCalled();
  });

  it('shows loading spinner when loading', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        canSend={true}
        isLoading={true}
      />
    );
    
    const spinner = screen.getByRole('progressbar');
    expect(spinner).toBeInTheDocument();
  });

  it('disables all buttons when loading', () => {
    render(
      <InputControls 
        onSend={mockOnSend} 
        onAttach={mockOnAttach}
        onVoice={mockOnVoice}
        canSend={true}
        isLoading={true}
        enableAttachment={true}
        enableVoice={true}
      />
    );
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    const attachButton = screen.getByRole('button', { name: /attach file/i });
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    
    expect(sendButton).toBeDisabled();
    expect(attachButton).toBeDisabled();
    expect(voiceButton).toBeDisabled();
  });

  it('applies correct styling to send button based on state', () => {
    const { rerender } = render(
      <InputControls onSend={mockOnSend} canSend={false} />
    );
    
    let sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
    
    rerender(<InputControls onSend={mockOnSend} canSend={true} />);
    
    sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeEnabled();
  });
});