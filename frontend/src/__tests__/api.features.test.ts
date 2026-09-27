import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError, isNotFoundError } from '../services/api';
import type { CopilotResponse, ReportJobResponse, RiskScoreResponse } from '../types';

function jsonResponse(body: unknown, status = 200, statusText = 'OK') {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: async () => body,
  } as Response;
}

const COPILOT_ANSWER: CopilotResponse = {
  answer: 'Three wallets received the stolen funds.',
  citations: [
    {
      type: 'trace',
      reference_id: 'trace-1',
      summary: 'Bounded trace of 3 hops',
      detail: null,
      confidence: 0.8,
    },
  ],
  confidence: 0.72,
  type: 'grounded_answer',
};

const RISK_SCORE: RiskScoreResponse = {
  risk_score_id: 'risk-1',
  case_id: 'case-1',
  trace_id: 'trace-1',
  wallet_address: '0xabc',
  score: 64,
  risk_category: 'high',
  scoring_version: 'v1',
  factors: [],
  calculated_at: '2026-09-26T00:00:00Z',
};

describe('Copilot / Risk / Report API functions', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('posts the question to the copilot ask endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(COPILOT_ANSWER));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.askCopilot('case-1', 'Which wallets received funds?');

    expect(result).toEqual(COPILOT_ANSWER);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/cases/case-1/copilot/ask');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ question: 'Which wallets received funds?' });
    expect(init.headers['Content-Type']).toBe('application/json');
  });

  it('posts an empty body to summarize', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(COPILOT_ANSWER));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await api.summarizeCase('case-1');

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/cases/case-1/copilot/summarize');
    expect(init.body).toBe('{}');
  });

  it('posts wallet_address to explain_risk', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(COPILOT_ANSWER));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await api.explainRisk('case-1', { wallet_address: '0xabc' });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/cases/case-1/copilot/explain_risk');
    expect(JSON.parse(init.body)).toEqual({ wallet_address: '0xabc' });
  });

  it('surfaces PROVIDER_ERROR from a 502 copilot failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse(
        { error: { code: 'PROVIDER_ERROR', message: 'LLM provider unavailable' } },
        502,
        'Bad Gateway',
      ),
    ) as unknown as typeof fetch;

    await expect(api.askCopilot('case-1', 'hello')).rejects.toMatchObject({
      name: 'ApiError',
      code: 'PROVIDER_ERROR',
      status: 502,
    });
  });

  it('fetches a wallet risk score', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(RISK_SCORE));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.getWalletRisk('case-1', '0xAbC');

    expect(result).toEqual(RISK_SCORE);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/case-1/wallets/0xAbC/risk');
  });

  it('fetches a risk explanation by risk score id', async () => {
    const explanation = {
      risk_score_id: 'risk-1',
      wallet_address: '0xabc',
      total_score: 64,
      risk_category: 'high',
      scoring_version: 'v1',
      factor_explanations: ['Fan-out pattern detected'],
      summary: 'Elevated risk driven by fan-out.',
      calculated_at: '2026-09-26T00:00:00Z',
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(explanation));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.getRiskExplanation('risk-1');

    expect(result).toEqual(explanation);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/risk/risk-1/explanation');
  });

  it('fetches the case risk summary', async () => {
    const summary = {
      case_id: 'case-1',
      trace_id: 'trace-1',
      wallet_count: 7,
      risk_distribution: { low: 4, high: 3 },
      highest_risk_wallet: '0xdef',
      highest_risk_score: 88,
      average_score: 41.5,
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(summary));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.getCaseRiskSummary('case-1');

    expect(result).toEqual(summary);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/case-1/risk-summary');
  });

  it('posts a report generation job and returns the 202 payload', async () => {
    const job: ReportJobResponse = {
      job_id: 'job-1',
      status: 'queued',
      message: 'Report generation job queued',
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(job, 202, 'Accepted'));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.generateReport('case-1', {
      report_type: 'detailed',
      format: 'json',
    });

    expect(result).toEqual(job);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/cases/case-1/reports');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ report_type: 'detailed', format: 'json' });
  });

  it('lists reports for a case', async () => {
    const list = {
      reports: [
        {
          report_id: 'rep-1',
          report_type: 'summary',
          format: 'json',
          generated_at: '2026-09-26T00:00:00Z',
          file_url: '/api/v1/reports/rep-1/download',
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(list));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.listReports('case-1');

    expect(result).toEqual(list);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/case-1/reports');
  });

  it('surfaces PDF_RENDERER_UNAVAILABLE verbatim from report generation', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          detail: {
            error: {
              code: 'PDF_RENDERER_UNAVAILABLE',
              message: 'No PDF renderer library installed',
            },
          },
        },
        500,
        'Internal Server Error',
      ),
    ) as unknown as typeof fetch;

    let thrown: unknown;
    try {
      await api.generateReport('case-1', { report_type: 'summary', format: 'pdf' });
    } catch (error) {
      thrown = error;
    }

    expect(thrown).toBeInstanceOf(ApiError);
    expect((thrown as ApiError).code).toBe('PDF_RENDERER_UNAVAILABLE');
  });

  it('identifies not-found failures for empty risk states', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse(
        { detail: { error: { code: 'NO_TRACE', message: 'No trace found for case' } } },
        404,
        'Not Found',
      ),
    ) as unknown as typeof fetch;

    let thrown: unknown;
    try {
      await api.getWalletRisk('case-1', '0xabc');
    } catch (error) {
      thrown = error;
    }

    expect(isNotFoundError(thrown)).toBe(true);
    expect(isNotFoundError(new ApiError('boom', 'PROVIDER_ERROR'))).toBe(false);
    expect(isNotFoundError('not-an-error')).toBe(false);
  });

  it('fetches case patterns with demo/live provenance flags', async () => {
    const body = {
      patterns: [
        {
          pattern_id: 'p-1',
          trace_id: 'trace-1',
          wallet_address: '0xabc',
          pattern_type: 'rapid_forwarding',
          demo_label: 'HIGH_TRANSACTION_VELOCITY',
          confidence: 0.7,
          description: 'DEMO DATA | synthetic_demo',
          metrics: { demo_data: true },
          detected_at: '2026-09-26T00:00:00Z',
          demo_data: true,
          finding_source: 'demo',
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(body));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.getCasePatterns('case-1');

    expect(result.patterns[0].demo_data).toBe(true);
    expect(result.patterns[0].finding_source).toBe('demo');
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/case-1/patterns');
  });

  it('fetches case evidence with provenance flags', async () => {
    const body = {
      evidence: [
        {
          evidence_id: 'e-1',
          evidence_type: 'note',
          reference_id: 'case-1',
          investigator_note: '[DEMO DATA] demo_data=true | synthetic note',
          pinned_at: '2026-09-26T00:00:00Z',
          demo_data: true,
          finding_source: 'demo',
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(body));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.getCaseEvidence('case-1');

    expect(result.evidence[0].demo_data).toBe(true);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/case-1/evidence');
  });

  it('fetches case attributions with provenance flags', async () => {
    const body = {
      attributions: [
        {
          attribution_id: 'a-1',
          trace_id: 'trace-1',
          wallet_address: '0xabc',
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
          disclaimer: 'synthetic demonstration classification',
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(body));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.getCaseAttributions('case-1');

    expect(result.attributions[0].entity_name).toBe('DEMO_EXCHANGE_A');
    expect(result.attributions[0].demo_data).toBe(true);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/cases/case-1/attributions');
  });
});
