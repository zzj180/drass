import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CharacterCounter } from '../CharacterCounter';

describe('CharacterCounter', () => {
  it('renders character count', () => {
    render(<CharacterCounter current={50} max={100} />);
    
    expect(screen.getByText('50 / 100')).toBeInTheDocument();
  });

  it('formats large numbers with commas', () => {
    render(<CharacterCounter current={1500} max={4096} />);
    
    expect(screen.getByText('1,500 / 4,096')).toBeInTheDocument();
  });

  it('shows progress bar when showProgress is true and above threshold', () => {
    render(<CharacterCounter current={60} max={100} showProgress={true} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '60');
  });

  it('hides progress bar when below 50% by default', () => {
    render(<CharacterCounter current={40} max={100} showProgress={true} />);
    
    const progressBar = screen.queryByRole('progressbar');
    expect(progressBar).not.toBeInTheDocument();
  });

  it('hides progress bar when showProgress is false', () => {
    render(<CharacterCounter current={80} max={100} showProgress={false} />);
    
    const progressBar = screen.queryByRole('progressbar');
    expect(progressBar).not.toBeInTheDocument();
  });

  it('applies warning color when near limit (>80%)', () => {
    render(<CharacterCounter current={85} max={100} />);
    
    const counter = screen.getByText('85 / 100');
    const parent = counter.closest('div');
    expect(parent).toBeInTheDocument();
    
    // Progress bar should have warning color
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('applies error color when at or over limit', () => {
    render(<CharacterCounter current={100} max={100} />);
    
    const counter = screen.getByText('100 / 100');
    const parent = counter.closest('div');
    expect(parent).toBeInTheDocument();
    
    // Progress bar should have error color
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('handles over-limit gracefully', () => {
    render(<CharacterCounter current={110} max={100} />);
    
    expect(screen.getByText('110 / 100')).toBeInTheDocument();
    
    const progressBar = screen.getByRole('progressbar');
    // Should cap at 100%
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });

  it('applies custom className', () => {
    const { container } = render(
      <CharacterCounter current={50} max={100} className="custom-counter" />
    );
    
    const counterElement = container.querySelector('.custom-counter');
    expect(counterElement).toBeInTheDocument();
  });

  it('shows progress bar at exactly 50%', () => {
    render(<CharacterCounter current={50} max={100} showProgress={true} />);
    
    const progressBar = screen.queryByRole('progressbar');
    expect(progressBar).not.toBeInTheDocument(); // Should not show at exactly 50%
  });

  it('shows progress bar at 51%', () => {
    render(<CharacterCounter current={51} max={100} showProgress={true} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '51');
  });

  it('renders with zero values', () => {
    render(<CharacterCounter current={0} max={100} />);
    
    expect(screen.getByText('0 / 100')).toBeInTheDocument();
  });

  it('applies correct text color based on percentage', () => {
    const { rerender } = render(<CharacterCounter current={50} max={100} />);
    
    // Normal color (< 80%)
    let counter = screen.getByText('50 / 100');
    expect(counter).toBeInTheDocument();
    
    // Warning color (80-99%)
    rerender(<CharacterCounter current={85} max={100} />);
    counter = screen.getByText('85 / 100');
    expect(counter).toBeInTheDocument();
    
    // Error color (>= 100%)
    rerender(<CharacterCounter current={100} max={100} />);
    counter = screen.getByText('100 / 100');
    expect(counter).toBeInTheDocument();
  });
});