import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError } from '../services/api';

describe('API Client Layer', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches cases successfully', async () => {
    const mockCases = [
      {
        case_id: '123',
        case_number: 'CASE-001',
        title: 'Test Incident',
        reported_wallet_address: '0xabc',
        blockchain: 'ethereum',
        fraud_type: 'investment_scam',
        status: 'active',
        investigator_id: 'inv-1',
        created_at: '2026-09-23T00:00:00Z',
        updated_at: '2026-09-23T00:00:00Z',
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCases,
    } as Response);

    const result = await api.getCases();
    expect(result).toEqual(mockCases);
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/v1/cases', expect.any(Object));
  });

  it('throws ApiError on HTTP failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({
        error: { code: 'NOT_FOUND', message: 'Case does not exist' },
      }),
    } as Response);

    await expect(api.getCaseById('non-existent')).rejects.toThrow(ApiError);
  });
});
