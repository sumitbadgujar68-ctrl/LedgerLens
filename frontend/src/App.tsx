import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sidebar } from './components/layout/Sidebar';
import { InvestigationLanding } from './components/landing/InvestigationLanding';
import { Dashboard } from './components/dashboard/Dashboard';
import { InvestigationWorkspace } from './components/workspace/InvestigationWorkspace';
import { EvidenceCustody } from './components/evidence/EvidenceCustody';
import { KnownAddresses } from './components/labels/KnownAddresses';
import { Settings } from './components/settings/Settings';
import { LoginPage } from './components/auth/LoginPage';
import { NewCaseModal } from './components/cases/NewCaseModal';
import { useInvestigationStore } from './store/investigationStore';
import { getToken, setSession, UNAUTHORIZED_EVENT, SIGNOUT_EVENT } from './services/auth';
import type { LoginResponse } from './services/auth';
import type { CaseCreatePayload } from './types';
import { api } from './services/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2,
    },
  },
});

import { TopNav } from './components/layout/TopNav';

function AuthenticatedShell() {
  const { isNewCaseModalOpen, setNewCaseModalOpen } = useInvestigationStore();
  const client = useQueryClient();
  const navigate = useNavigate();

  const createMutation = useMutation({
    mutationFn: (payload: CaseCreatePayload) => api.createCase(payload),
    onSuccess: (newCase) => {
      client.invalidateQueries({ queryKey: ['cases'] });
      setNewCaseModalOpen(false);
      navigate(`/cases/${newCase.case_id}`);
    },
  });

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--bg-app)] text-[var(--text-main)] font-sans antialiased">
      <Sidebar />

      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <TopNav />
        <Routes>
          {/* Investigation-first landing page */}
          <Route path="/" element={<InvestigationLanding />} />

          {/* Full case registry */}
          <Route path="/cases" element={<Dashboard />} />
          <Route path="/investigations" element={<Dashboard />} />

          {/* Primary Forensic Investigation Workspace */}
          <Route path="/cases/:caseId" element={<InvestigationWorkspace />} />
          <Route path="/cases/:caseId/:view" element={<InvestigationWorkspace />} />

          {/* Supporting views */}
          <Route path="/labels" element={<KnownAddresses />} />
          <Route path="/attribution" element={<KnownAddresses />} />
          <Route path="/evidence" element={<EvidenceCustody />} />
          <Route path="/settings" element={<Settings />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      <NewCaseModal
        isOpen={isNewCaseModalOpen}
        onClose={() => setNewCaseModalOpen(false)}
        onSubmit={async (payload) => {
          await createMutation.mutateAsync(payload);
        }}
      />
    </div>
  );
}

function AuthenticatedApp() {
  return (
    <BrowserRouter>
      <AuthenticatedShell />
    </BrowserRouter>
  );
}

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => !!getToken());
  const [isInitializing, setIsInitializing] = useState<boolean>(() => !getToken());

  useEffect(() => {
    if (!getToken()) {
      setIsInitializing(true);
      api.login('demo@ledgerlens.local', 'LedgerLens2026!')
        .then((session: LoginResponse) => {
          setSession(session.access_token, session.investigator);
          setIsAuthenticated(true);
        })
        .catch((err: unknown) => {
          console.warn('Auto-login failed, falling back to login screen:', err);
          setIsAuthenticated(false);
        })
        .finally(() => {
          setIsInitializing(false);
        });
    }
  }, []);

  const handleLoginSuccess = useCallback(() => {
    setIsAuthenticated(true);
  }, []);

  // Handle explicit sign-out
  useEffect(() => {
    const handleSignOutEvent = () => {
      setIsAuthenticated(false);
    };
    window.addEventListener(SIGNOUT_EVENT, handleSignOutEvent);
    return () => window.removeEventListener(SIGNOUT_EVENT, handleSignOutEvent);
  }, []);

  // Listen for unauthorized events (expired/invalid tokens) and attempt seamless re-login
  useEffect(() => {
    const handleUnauthorized = () => {
      api.login('demo@ledgerlens.local', 'LedgerLens2026!')
        .then((session: LoginResponse) => {
          setSession(session.access_token, session.investigator);
          setIsAuthenticated(true);
        })
        .catch(() => {
          setIsAuthenticated(false);
        });
    };
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, []);

  if (isInitializing) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#090d12] text-[#388bfd]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-[#388bfd] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
            AUTHENTICATING INVESTIGATOR CONSOLE...
          </span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <QueryClientProvider client={queryClient}>
        <LoginPage onSuccess={handleLoginSuccess} />
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AuthenticatedApp />
    </QueryClientProvider>
  );
}

export default App;

