import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { CopilotPanel } from '../components/copilot/CopilotPanel';
import { api, ApiError } from '../services/api';
import type { CopilotResponse } from '../types';

function renderPanel(props: { selectedWalletAddress?: string | null } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <CopilotPanel caseId="case-1" {...props} />
    </QueryClientProvider>,
  );
}

const ANSWER: CopilotResponse = {
  answer: 'The seed wallet fanned out to three hop-1 wallets.',
  citations: [
    {
      type: 'trace',
      reference_id: 'trace-1',
      summary: 'Bounded trace covering 3 hops',
      detail: null,
      confidence: 0.8,
    },
  ],
  confidence: 0.72,
  type: 'grounded_answer',
};

describe('CopilotPanel states', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows the empty state before any question is asked', () => {
    renderPanel();
    expect(screen.getByText(/ask the case copilot/i)).toBeTruthy();
    expect(screen.queryByTestId('copilot-answer')).toBeNull();
    expect(screen.getByText('AI-GENERATED')).toBeTruthy();
  });

  it('renders an AI answer with provenance badge, citations and confidence meter', async () => {
    vi.spyOn(api, 'askCopilot').mockResolvedValue(ANSWER);
    renderPanel();

    const input = screen.getByPlaceholderText(/ask about this case/i);
    fireEvent.change(input, { target: { value: 'Where did the funds go?' } });
    fireEvent.click(screen.getByTitle('Send question'));

    await waitFor(() => {
      expect(screen.getByTestId('copilot-answer')).toBeTruthy();
    });

    expect(api.askCopilot).toHaveBeenCalledWith('case-1', 'Where did the funds go?');
    expect(screen.getByText(ANSWER.answer)).toBeTruthy();
    expect(screen.getAllByText('AI-GENERATED').length).toBeGreaterThan(1);
    expect(screen.getByText('CONFIDENCE')).toBeTruthy();
    expect(screen.getByText('72%')).toBeTruthy();

    expect(screen.getByText('trace')).toBeTruthy();
    expect(screen.getByText('Bounded trace covering 3 hops')).toBeTruthy();
    expect(screen.getByText(/citations \(1\)/i)).toBeTruthy();
  });

  it('surfaces ApiError codes such as PROVIDER_ERROR in the thread', async () => {
    vi.spyOn(api, 'askCopilot').mockRejectedValue(
      new ApiError('LLM provider unavailable', 'PROVIDER_ERROR'),
    );
    renderPanel();

    fireEvent.change(screen.getByPlaceholderText(/ask about this case/i), {
      target: { value: 'hello' },
    });
    fireEvent.click(screen.getByTitle('Send question'));

    await waitFor(() => {
      expect(screen.getByTestId('copilot-error')).toBeTruthy();
    });

    expect(screen.getByText('PROVIDER_ERROR')).toBeTruthy();
    expect(screen.getByText('LLM provider unavailable')).toBeTruthy();
    expect(screen.queryByTestId('copilot-answer')).toBeNull();
  });

  it('reports insufficient-data 200 responses honestly instead of inventing text', async () => {
    vi.spyOn(api, 'askCopilot').mockResolvedValue({
      answer: '',
      citations: [],
      confidence: 0,
      type: 'insufficient_data',
    });
    renderPanel();

    fireEvent.change(screen.getByPlaceholderText(/ask about this case/i), {
      target: { value: 'Tell me about unknown data' },
    });
    fireEvent.click(screen.getByTitle('Send question'));

    await waitFor(() => {
      expect(screen.getByTestId('copilot-answer')).toBeTruthy();
    });

    expect(screen.getByText(/insufficient case data/i)).toBeTruthy();
    expect(screen.getByText('insufficient_data')).toBeTruthy();
  });

  it('disables Explain risk until a wallet is selected and passes the wallet address', async () => {
    vi.spyOn(api, 'explainRisk').mockResolvedValue(ANSWER);

    const { unmount } = renderPanel({ selectedWalletAddress: null });
    const disabledButton = screen.getByTitle(/select a wallet in the graph first/i);
    expect((disabledButton as HTMLButtonElement).disabled).toBe(true);
    unmount();

    renderPanel({ selectedWalletAddress: '0xWallet' });
    const enabledButton = screen.getByTitle(/ask the copilot to explain risk/i);
    expect((enabledButton as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(enabledButton);

    await waitFor(() => {
      expect(api.explainRisk).toHaveBeenCalledWith('case-1', {
        wallet_address: '0xWallet',
      });
    });
  });

  it('sends the summarize action without a question', async () => {
    vi.spyOn(api, 'summarizeCase').mockResolvedValue(ANSWER);
    renderPanel();

    fireEvent.click(screen.getAllByText('Summarize case')[0]);

    await waitFor(() => {
      expect(api.summarizeCase).toHaveBeenCalledWith('case-1');
    });
  });
});
