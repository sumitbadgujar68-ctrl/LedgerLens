import React, { useState } from "react";
import { api, ApiError } from "../../services/api";
import { setSession } from "../../services/auth";
import { Radar, Shield } from "lucide-react";

interface LoginPageProps {
  onSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState("demo@ledgerlens.local");
  const [password, setPassword] = useState("LedgerLens2026!");
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
          : "Sign-in failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickDemo = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const session = await api.login("demo@ledgerlens.local", "LedgerLens2026!");
      setSession(session.access_token, session.investigator);
      onSuccess();
    } catch (err) {
      setError("Demo authentication failed. Ensure backend is running.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-[#090B10] text-slate-100 font-[Inter]">
      <div className="w-full max-w-md px-6">
        <div className="mb-8 text-center space-y-3">
          <div className="flex items-center justify-center">
            <div className="w-14 h-14 rounded-lg bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400 shadow-lg shadow-blue-900/20">
              <Radar className="w-8 h-8" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-wider">LEDGERLENS</h1>
            <p className="mt-1 text-[11px] text-slate-400 font-bold uppercase tracking-widest">
              Investigation console
            </p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-lg border border-[#1F2637] bg-[#121620] p-6 shadow-2xl shadow-black/20"
        >
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-slate-100">
              Investigator sign-in
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400 mb-5">
            Authenticate to access cases, traces and reports.
          </p>

          <label
            className="block text-xs font-medium text-slate-300"
            htmlFor="username"
          >
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
            className="mt-1 w-full rounded border border-[var(--color-outline)] bg-[var(--color-surface-dim)] px-3 py-2 font-[Inter] text-sm text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)] focus:border-[var(--color-primary)] focus:outline-none transition-colors"
            placeholder="investigator@agency.gov"
          />

          <label
            className="mt-4 block text-xs font-medium text-slate-300"
            htmlFor="password"
          >
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
            className="mt-1 w-full rounded border border-[var(--color-outline)] bg-[var(--color-surface-dim)] px-3 py-2 font-[Inter] text-sm text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)] focus:border-[var(--color-primary)] focus:outline-none transition-colors"
            placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
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
            className="mt-6 w-full rounded bg-blue-600 px-4 py-2.5 text-sm font-semibold text-[var(--color-on-surface)] transition-all hover:bg-blue-500 hover:shadow-lg hover:shadow-blue-900/30 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>

          <button
            type="button"
            onClick={handleQuickDemo}
            disabled={submitting}
            className="mt-3 w-full rounded border border-blue-500/40 bg-blue-950/30 px-4 py-2 text-xs font-semibold text-blue-400 hover:bg-blue-900/40 transition-colors cursor-pointer"
          >
            Quick 1-Click Demo Investigator Access
          </button>
        </form>

        <p className="mt-4 text-center font-semibold text-[11px] text-slate-500">
          ACCESS IS RESTRICTED TO AUTHORIZED INVESTIGATORS
        </p>
        <p className="mt-1 text-center font-semibold text-[10px] text-slate-600">
          SIH 2026 {"·"} PS SIH26183
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
