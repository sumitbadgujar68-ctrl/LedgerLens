import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from './components/layout/Sidebar';
import { Dashboard } from './components/dashboard/Dashboard';
import { InvestigationWorkspace } from './components/workspace/InvestigationWorkspace';
import { EvidenceCustody } from './components/evidence/EvidenceCustody';
import { Settings } from './components/settings/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen w-screen overflow-hidden bg-[#090B10] text-slate-100 font-sans">
          <Sidebar />

          <div className="flex-1 flex flex-col h-full overflow-hidden">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/cases" element={<Navigate to="/" replace />} />
              <Route path="/cases/:caseId" element={<InvestigationWorkspace />} />
              <Route path="/evidence" element={<EvidenceCustody />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
