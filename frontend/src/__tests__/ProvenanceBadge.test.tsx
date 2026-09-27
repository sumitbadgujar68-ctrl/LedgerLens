import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';

describe('ProvenanceBadge', () => {
  it('renders the DEMO DATA variant with amber styling', () => {
    render(<ProvenanceBadge variant="demo" />);
    const badge = screen.getByText('DEMO DATA');
    expect(badge).toBeTruthy();
    expect(badge.className).toContain('text-amber-400');
    expect(badge.className).toContain('bg-amber-950/60');
  });

  it('renders the LIVE ON-CHAIN variant with emerald styling', () => {
    render(<ProvenanceBadge variant="live" />);
    const badge = screen.getByText('LIVE ON-CHAIN');
    expect(badge).toBeTruthy();
    expect(badge.className).toContain('text-emerald-400');
    expect(badge.className).toContain('bg-emerald-950/60');
  });

  it('renders the AI-GENERATED variant with violet styling', () => {
    render(<ProvenanceBadge variant="ai" />);
    const badge = screen.getByText('AI-GENERATED');
    expect(badge).toBeTruthy();
    expect(badge.className).toContain('text-violet-400');
    expect(badge.className).toContain('bg-violet-950/60');
  });

  it('falls back to the demo styling for an unknown variant', () => {
    render(<ProvenanceBadge variant={'bogus' as 'demo'} />);
    expect(screen.getByText('DEMO DATA')).toBeTruthy();
  });

  it('appends a custom className', () => {
    render(<ProvenanceBadge variant="demo" className="custom-marker" />);
    expect(screen.getByText('DEMO DATA').className).toContain('custom-marker');
  });
});
