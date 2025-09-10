import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingIndicator } from '../LoadingIndicator';

describe('LoadingIndicator', () => {
  it('renders dots indicator by default', () => {
    const { container } = render(<LoadingIndicator />);
    
    // Should have 3 dots
    const dots = container.querySelectorAll('[style*="border-radius: 50%"]');
    expect(dots).toHaveLength(3);
  });

  it('renders circular progress when type is circular', () => {
    render(<LoadingIndicator type="circular" />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toBeInTheDocument();
  });

  it('renders linear progress when type is linear', () => {
    render(<LoadingIndicator type="linear" />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toBeInTheDocument();
  });

  it('renders skeleton when type is skeleton', () => {
    const { container } = render(<LoadingIndicator type="skeleton" />);
    
    const skeletons = container.querySelectorAll('.MuiSkeleton-root');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders text when provided', () => {
    render(<LoadingIndicator text="Loading data..." />);
    
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('applies small size correctly', () => {
    const { container } = render(<LoadingIndicator type="dots" size="small" />);
    
    const dots = container.querySelectorAll('[style*="width: 6px"]');
    expect(dots).toHaveLength(3);
  });

  it('applies medium size correctly', () => {
    const { container } = render(<LoadingIndicator type="dots" size="medium" />);
    
    const dots = container.querySelectorAll('[style*="width: 8px"]');
    expect(dots).toHaveLength(3);
  });

  it('applies large size correctly', () => {
    const { container } = render(<LoadingIndicator type="dots" size="large" />);
    
    const dots = container.querySelectorAll('[style*="width: 10px"]');
    expect(dots).toHaveLength(3);
  });

  it('applies custom className', () => {
    const { container } = render(
      <LoadingIndicator className="custom-loading" />
    );
    
    expect(container.querySelector('.custom-loading')).toBeInTheDocument();
  });

  it('renders different text sizes based on size prop', () => {
    const { rerender } = render(
      <LoadingIndicator size="small" text="Loading..." />
    );
    
    let text = screen.getByText('Loading...');
    expect(text).toHaveStyle({ fontSize: '0.75rem' });
    
    rerender(<LoadingIndicator size="medium" text="Loading..." />);
    
    text = screen.getByText('Loading...');
    expect(text).toHaveStyle({ fontSize: '0.875rem' });
  });

  it('renders circular progress with correct size', () => {
    render(<LoadingIndicator type="circular" size="small" />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('style');
    // Size should be applied through MUI's CircularProgress component
  });

  it('renders linear progress with full width container', () => {
    const { container } = render(<LoadingIndicator type="linear" />);
    
    const progressContainer = container.querySelector('[style*="width: 100%"]');
    expect(progressContainer).toBeInTheDocument();
  });

  it('applies animation to dots', () => {
    const { container } = render(<LoadingIndicator type="dots" />);
    
    const dots = container.querySelectorAll('[style*="animation"]');
    expect(dots).toHaveLength(3);
    
    // Check animation delays
    expect(dots[0]).toHaveStyle({ animationDelay: '0s' });
    expect(dots[1]).toHaveStyle({ animationDelay: '0.16s' });
    expect(dots[2]).toHaveStyle({ animationDelay: '0.32s' });
  });
});