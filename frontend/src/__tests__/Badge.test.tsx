import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { HopBadge, StatusBadge, AddressDisplay } from '../components/common/Badge';

describe('Badge and Address Components', () => {
  it('renders seed hop badge correctly', () => {
    render(<HopBadge hop={0} />);
    expect(screen.getByText('SEED (HOP 0)')).toBeTruthy();
  });

  it('renders intermediate hop badge correctly', () => {
    render(<HopBadge hop={2} />);
    expect(screen.getByText('HOP 2')).toBeTruthy();
  });

  it('renders status badge correctly', () => {
    render(<StatusBadge status="under_investigation" />);
    expect(screen.getByText(/under investigation/i)).toBeTruthy();
  });

  it('renders truncated address correctly', () => {
    const fullAddress = '0x1234567890123456789012345678901234567890';
    render(<AddressDisplay address={fullAddress} truncate={true} />);
    expect(screen.getByText('0x123456...567890')).toBeTruthy();
  });
});
