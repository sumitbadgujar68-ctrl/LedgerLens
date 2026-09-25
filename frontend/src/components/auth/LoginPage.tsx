import React, { useState } from 'react';
import { api, ApiError } from '../../services/api';
import { setSession } from '../../services/auth';

interface LoginPageProps {
  onSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const session = await api.login(username, password);
      setSession(session.access_token, session.investigator);
      onSuccess();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Sign-in failed. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-[#090B10] text-slate-100 font-sans">
      <div className="w-full max-w-md px-6">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">LedgerLens</h1>
          <p className="mt-1 font-mono text-xs text-slate-400">
            BLOCKCHAIN FRAUD INVESTIGATION WORKSTATION
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded border border-[#1F2637] bg-[#121620] p-6"
        >
          <h2 className="text-sm font-semibold text-slate-100">Investigator sign-in</h2>
          <p className="mt-1 text-xs text-slate-400">
            Authenticate to access cases, traces and reports.
          </p>

          <label className="mt-5 block text-xs font-medium text-slate-300" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="mt-1 w-full rounded border border-[#1F2637] bg-[#090B10] px-3 py-2 font-mono text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            placeholder="investigator@agency.gov"
          />

          <label className="mt-4 block text-xs font-medium text-slate-300" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded border border-[#1F2637] bg-[#090B10] px-3 py-2 font-mono text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            placeholder="••••••••"
          />

          {error && (
            <p
              role="alert"
              className="mt-4 rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-300"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-6 w-full rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-4 text-center font-mono text-[11px] text-slate-500">
          ACCESS IS RESTRICTED TO AUTHORIZED INVESTIGATORS
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
