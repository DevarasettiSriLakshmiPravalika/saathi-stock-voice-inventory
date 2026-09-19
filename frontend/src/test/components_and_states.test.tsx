import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';
import { LoadingSpinner } from '../components/LoadingSpinner';

describe('Frontend UI Components & States', () => {
  it('renders StatusBadge with correct text and no emojis', () => {
    const { rerender } = render(<StatusBadge status="CONFIRMED" />);
    expect(screen.getByText('CONFIRMED')).toBeInTheDocument();

    rerender(<StatusBadge status="FLAGGED" />);
    expect(screen.getByText('FLAGGED')).toBeInTheDocument();

    rerender(<StatusBadge status="REJECTED" />);
    expect(screen.getByText('REJECTED')).toBeInTheDocument();
  });

  it('renders EmptyState with title, description, and action button', () => {
    let clicked = false;
    render(
      <EmptyState
        title="No Inventory Available"
        description="Please record your first statement."
        actionLabel="Record Voice"
        onAction={() => {
          clicked = true;
        }}
      />
    );

    expect(screen.getByText('No Inventory Available')).toBeInTheDocument();
    expect(screen.getByText('Please record your first statement.')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: 'Record Voice' });
    btn.click();
    expect(clicked).toBe(true);
  });

  it('renders LoadingSpinner with custom message', () => {
    render(<LoadingSpinner message="Calculating stock balance..." />);
    expect(screen.getByText('Calculating stock balance...')).toBeInTheDocument();
  });
});
