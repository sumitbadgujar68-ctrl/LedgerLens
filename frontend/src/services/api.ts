import type { Case, CaseCreatePayload, TraceRequestPayload, TraceResponse } from '../types';
import { getToken, notifyUnauthorized } from './auth';
import type { Investigator, LoginResponse } from './auth';

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
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
    const envelope = errorData?.error || errorData?.detail?.error;
    const message = envelope?.message || errorData?.detail?.message || `HTTP error ${response.status}: ${response.statusText}`;
    const code = envelope?.code;
    const details = errorData?.error?.details || errorData?.detail?.error?.details;
    if (response.status === 401) {
      notifyUnauthorized();
    }
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

  async login(username: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  },

  async logout(): Promise<{ message: string }> {
    return request<{ message: string }>('/auth/logout', { method: 'POST' });
  },

  async me(): Promise<Investigator> {
    return request<Investigator>('/auth/me');
  },
};
