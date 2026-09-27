import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BottomDock } from '../components/dock/BottomDock';
import { useInvestigationStore } from '../store/investigationStore';
import { api } from '../services/api';
import type {
  AttributionListResponse,
  EvidenceListResponse,
  PatternListResponse,
} from '../types';

const PATTERNS: PatternListResponse = {
  patterns: [
    {
      pattern_id: 'p-demo',
      trace_id: 'trace-1',
      wallet_address: '0x2222222222222222222222222222222222222222',
      pattern_type: 'rapid_forwarding',
      demo_label: 'HIGH_TRANSACTION_VELOCITY',
      confidence: 0.7,
      description: 'DEMO DATA | synthetic_demo demonstration row',
      metrics: { demo_data: true },
      detected_at: '2026-09-26T00:00:00Z',
      demo_data: true,
      finding_source: 'demo',
    },
    {
      pattern_id: 'p-live',
      trace_id: 'trace-1',
      wallet_address: '0x3333333333333333333333333333333333333333',
      pattern_type: 'fan_out',
      confidence: 0.9,
      description: 'Fan-out derived from the live trace graph',
      metrics: {},
      detected_at: '2026-09-26T00:00:00Z',
      demo_data: false,
      finding_source: 'live_trace_derived',
    },
  ],
};

const ATTRIBUTIONS: AttributionListResponse = {
  attributions: [
    {
      attribution_id: 'a-demo',
      trace_id: 'trace-1',
      wallet_address: '0x4444444444444444444444444444444444444444',
      entity_id: 'ent-1',
      entity_name: 'DEMO_EXCHANGE_A',
      entity_type: 'exchange',
      provenance_level: 'INFERRED',
      confidence: 0.4,
      attribution_method: 'multi_signal',
      source: 'demo_seed',
      attributed_at: '2026-09-26T00:00:00Z',
      demo_data: true,
      finding_source: 'demo',
      disclaimer: 'Synthetic DEMO DATA classification, not a real service claim.',
    },
  ],
};

const EVIDENCE: EvidenceListResponse = {
  evidence: [
    {
      evidence_id: 'e-demo',
      evidence_type: 'note',
      reference_id: 'case-1',
      investigator_note: '[DEMO DATA] demo_data=true | synthetic analyst note',
      pinned_at: '2026-09-26T00:00:00Z',
      demo_data: true,
      finding_source: 'demo',
    },
    {
      evidence_id: 'e-live',
      evidence_type: 'wallet',
      reference_id: 'trace-1',
      investigator_note: 'Subject wallet traced via Ethereum Mainnet provider',
      pinned_at: '2026-09-26T00:00:00Z',
      demo_data: false,
      finding_source: 'live_on_chain',
    },
  ],
};

function renderDock() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BottomDock />
    </QueryClientProvider>,
  );
}

describe('BottomDock findings and evidence provenance', () => {
  beforeEach(() => {
    useInvestigationStore.setState({
      currentCase: {
        case_id: 'case-1',
        case_number: 'CASE-DEMO-001',
        title: 'Demo case',
        reported_wallet_address: '0x1111111111111111111111111111111111111111',
        blockchain: 'ethereum',
        fraud_type: 'investment_scam',
        status: 'under_investigation',
        investigator_id: 'inv-1',
        demo_data: true,
        created_at: '2026-09-26T00:00:00Z',
        updated_at: '2026-09-26T00:00:00Z',
      },
      activeBottomTab: 'ledger',
      evidenceNotes: [
        {
          id: 'note-1',
          caseId: 'case-1',
          timestamp: '2026-09-26T00:00:00Z',
          author: 'Demo Analyst',
          content: '[DEMO DATA] demo_data=true | seeded note',
          tag: 'lead',
        },
      ],
    });
    vi.restoreAllMocks();
    vi.spyOn(api, 'getCasePatterns').mockResolvedValue(PATTERNS);
    vi.spyOn(api, 'getCaseEvidence').mockResolvedValue(EVIDENCE);
    vi.spyOn(api, 'getCaseAttributions').mockResolvedValue(ATTRIBUTIONS);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders pattern and attribution rows with demo/live badges in FINDINGS', async () => {
    renderDock();

    fireEvent.click(screen.getByText(/FINDINGS \(/));

    await waitFor(() => {
      expect(screen.getByText('HIGH TRANSACTION VELOCITY')).toBeTruthy();
    });

    expect(api.getCasePatterns).toHaveBeenCalledWith('case-1');
    expect(api.getCaseAttributions).toHaveBeenCalledWith('case-1');

    expect(screen.getByText('fan out')).toBeTruthy();
    expect(screen.getByText('DEMO_EXCHANGE_A')).toBeTruthy();
    expect(screen.getByText(/synthetic DEMO DATA classification/i)).toBeTruthy();

    const demoBadges = screen.getAllByText('DEMO DATA');
    const liveBadges = screen.getAllByText('LIVE ON-CHAIN');
    expect(demoBadges.length).toBeGreaterThanOrEqual(2);
    expect(liveBadges.length).toBeGreaterThanOrEqual(1);
  });

  it('renders stored evidence rows with per-record provenance badges', async () => {
    renderDock();

    fireEvent.click(screen.getByText(/EVIDENCE \(/));

    await waitFor(() => {
      expect(screen.getByText(/\[DEMO DATA\] demo_data=true \| synthetic analyst note/)).toBeTruthy();
    });

    expect(api.getCaseEvidence).toHaveBeenCalledWith('case-1');
    expect(
      screen.getByText('Subject wallet traced via Ethereum Mainnet provider'),
    ).toBeTruthy();
    expect(screen.getAllByText('DEMO DATA').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('LIVE ON-CHAIN').length).toBeGreaterThanOrEqual(1);
  });

  it('shows an empty state when no findings are recorded', async () => {
    vi.spyOn(api, 'getCasePatterns').mockResolvedValue({ patterns: [] });
    vi.spyOn(api, 'getCaseAttributions').mockResolvedValue({ attributions: [] });

    renderDock();
    fireEvent.click(screen.getByText(/FINDINGS \(/));

    await waitFor(() => {
      expect(screen.getByText(/No pattern findings recorded/i)).toBeTruthy();
    });
    expect(screen.getByText(/No attributions recorded/i)).toBeTruthy();
  });
});
