import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, ApiError } from '../services/api';
import {
  getToken,
  setSession,
  UNAUTHORIZED_EVENT,
} from '../services/auth';

const INVESTIGATOR = {
  investigator_id: '00000000-0000-0000-0000-000000000001',
  username: 'investigator@test.local',
  full_name: 'Test Investigator',
  role: 'investigator',
};

function jsonResponse(body: unknown, status = 200, statusText = 'OK') {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: async () => body,
  } as Response;
}

describe('API auth regression (Phase 7)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it('attaches Authorization bearer header when a token is stored', async () => {
    setSession('stored-jwt-token', INVESTIGATOR);
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([]));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await api.getCases();

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer stored-jwt-token');
  });

  it('sends no Authorization header when no token is stored', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([]));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await api.getCases();

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });

  it('clears the session and emits the unauthorized event on HTTP 401', async () => {
    setSession('expired-jwt', INVESTIGATOR);
    const listener = vi.fn();
    window.addEventListener(UNAUTHORIZED_EVENT, listener);

    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(
          { detail: { error: { code: 'INVALID_TOKEN', message: 'Access token is invalid.' } } },
          401,
          'Unauthorized',
        ),
      ) as unknown as typeof fetch;

    await expect(api.getCases()).rejects.toThrow(ApiError);

    expect(getToken()).toBeNull();
    expect(listener).toHaveBeenCalledTimes(1);

    window.removeEventListener(UNAUTHORIZED_EVENT, listener);
  });

  it('surfaces the documented auth error envelope (detail.error)', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(
          { detail: { error: { code: 'INVALID_CREDENTIALS', message: 'Invalid username or password' } } },
          401,
          'Unauthorized',
        ),
      ) as unknown as typeof fetch;

    let thrown: unknown;
    try {
      await api.login('investigator@test.local', 'wrong-password');
    } catch (error) {
      thrown = error;
    }

    expect(thrown).toBeInstanceOf(ApiError);
    const apiError = thrown as ApiError;
    expect(apiError.code).toBe('INVALID_CREDENTIALS');
    expect(apiError.message).toBe('Invalid username or password');
  });

  it('surfaces the legacy top-level error envelope unchanged', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(
          { error: { code: 'CASE_NOT_FOUND', message: 'Case not found' } },
          404,
          'Not Found',
        ),
      ) as unknown as typeof fetch;

    await expect(api.getCaseById('missing-case')).rejects.toMatchObject({
      code: 'CASE_NOT_FOUND',
      message: 'Case not found',
    });
  });
});
