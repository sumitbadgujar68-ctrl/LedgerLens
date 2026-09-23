import type { Case, CaseCreatePayload, TraceRequestPayload, TraceResponse } from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  code?: string;
  details?: Record<string, unknown>;
  
  constructor(message: string, code?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      // ignore
    }
    const message = errorData?.error?.message || errorData?.detail || `HTTP error ${response.status}: ${response.statusText}`;
    const code = errorData?.error?.code;
    const details = errorData?.error?.details;
    throw new ApiError(message, code, details);
  }

  return response.json();
}

export const api = {
  async getCases(params?: { status?: string; blockchain?: string }): Promise<Case[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.blockchain) searchParams.append('blockchain', params.blockchain);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return request<Case[]>(`/cases${query}`);
  },

  async getCaseById(caseId: string): Promise<Case> {
    return request<Case>(`/cases/${caseId}`);
  },

  async createCase(payload: CaseCreatePayload): Promise<Case> {
    return request<Case>('/cases', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateCase(caseId: string, payload: Partial<Case>): Promise<Case> {
    return request<Case>(`/cases/${caseId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async runTrace(caseId: string, payload: TraceRequestPayload): Promise<TraceResponse> {
    return request<TraceResponse>(`/cases/${caseId}/traces`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getTraces(caseId: string): Promise<TraceResponse[]> {
    return request<TraceResponse[]>(`/cases/${caseId}/traces`);
  },

  async getTraceById(caseId: string, traceId: string): Promise<TraceResponse> {
    return request<TraceResponse>(`/cases/${caseId}/traces/${traceId}`);
  },
};
