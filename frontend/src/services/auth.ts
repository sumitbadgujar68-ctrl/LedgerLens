export interface Investigator {
  investigator_id: string;
  username: string;
  full_name: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  investigator: Investigator;
}

const TOKEN_KEY = 'ledgerlens.token';
const USER_KEY = 'ledgerlens.investigator';

export const UNAUTHORIZED_EVENT = 'ledgerlens:unauthorized';
export const SIGNOUT_EVENT = 'ledgerlens:signout';

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getInvestigator(): Investigator | null {
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as Investigator) : null;
  } catch {
    return null;
  }
}

export function setSession(token: string, investigator: Investigator): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(investigator));
  } catch {
    // storage unavailable: session stays in memory for this tab only
  }
}

export function clearSession(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
  } catch {
    // storage unavailable: nothing to clear
  }
}

export function notifyUnauthorized(): void {
  clearSession();
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
}

export function notifySignOut(): void {
  clearSession();
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(SIGNOUT_EVENT));
  }
}
