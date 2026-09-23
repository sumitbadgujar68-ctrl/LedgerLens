import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useInvestigationStore } from '../../store/investigationStore';
import { FundFlowCanvas } from '../graph/FundFlowCanvas';
import { InspectorDrawer } from '../inspector/InspectorDrawer';
import { BottomDock } from '../dock/BottomDock';
import { AddressDisplay, StatusBadge } from '../common/Badge';
import { 
  ArrowLeft, 
  Play, 
  AlertCircle,
  Download,
} from 'lucide-react';
import type { TraceRequestPayload } from '../../types';

export const InvestigationWorkspace: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();

  const {
    setCurrentCase,
    currentTrace,
    setCurrentTrace,
  } = useInvestigationStore();

  const [direction] = useState<'outbound' | 'inbound' | 'both'>('outbound');
  const [maxHops, setMaxHops] = useState<number>(3);
  const [maxBranches] = useState<number>(25);
  const [minAmount] = useState<string>('');

  const { data: caseData, isLoading: caseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => api.getCaseById(caseId!),
    enabled: !!caseId,
  });

  const { data: tracesData, refetch: refetchTraces } = useQuery({
    queryKey: ['traces', caseId],
    queryFn: () => api.getTraces(caseId!),
    enabled: !!caseId,
  });

  useEffect(() => {
    if (caseData) {
      setCurrentCase(caseData);
    }
  }, [caseData, setCurrentCase]);

  useEffect(() => {
    if (tracesData && tracesData.length > 0) {
      setCurrentTrace(tracesData[0]);
    }
  }, [tracesData, setCurrentTrace]);

  const traceMutation = useMutation({
    mutationFn: (payload: TraceRequestPayload) => api.runTrace(caseId!, payload),
    onSuccess: (traceResult) => {
      setCurrentTrace(traceResult);
      refetchTraces();
    },
  });

  const handleExecuteTrace = () => {
    if (!caseData) return;
    traceMutation.mutate({
      start_wallet_address: caseData.reported_wallet_address,
      direction,
      max_hops: maxHops,
      max_branches: maxBranches,
      min_amount: minAmount ? Number(minAmount) : null,
    });
  };

  const handleExportBrief = () => {
    if (!caseData) return;
    const briefContent = `========================================================
LEDGERLENS FORENSIC INCIDENT DOSSIER
========================================================
Case Number: ${caseData.case_number}
Title: ${caseData.title}
Blockchain: ${caseData.blockchain.toUpperCase()}
Fraud Typology: ${caseData.fraud_type}
Reported Seed Address: ${caseData.reported_wallet_address}
Reported Tx Hash: ${caseData.reported_transaction_hash || 'N/A'}
Reported Loss: ${caseData.reported_amount ?? 'N/A'} ${caseData.reported_asset || ''}
Status: ${caseData.status}
Creation Date: ${new Date(caseData.created_at).toUTCString()}

CANONICAL GRAPH SUMMARY:
Discovered Wallets: ${currentTrace?.summary?.wallet_count ?? 0}
Transfers Traced: ${currentTrace?.summary?.transaction_count ?? 0}
Max Hop Depth: ${currentTrace?.summary?.max_hop_depth ?? 0}
Provider: ${currentTrace?.provider || 'AlchemyProvider'}
========================================================
`;
    const blob = new Blob([briefContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${caseData.case_number}_Forensic_Brief.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (caseLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#090B10] text-slate-400 font-mono text-sm">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-3" />
        Loading Investigation Workspace...
      </div>
    );
  }

  if (caseError || !caseData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#090B10] text-slate-300 p-6 font-mono">
        <AlertCircle className="w-12 h-12 text-red-400 mb-3" />
        <h2 className="text-base font-bold text-slate-100">Case Docket Not Found</h2>
        <p className="text-xs text-slate-400 mt-1 mb-4">
          Unable to locate case {caseId}. It may have been removed or archived.
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded"
        >
          Return to Dispatch Console
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#090B10]">
      <header className="bg-[#0D1017] border-b border-[#1F2637] px-6 py-3 shrink-0 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors cursor-pointer"
            title="Return to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-blue-400">
                {caseData.case_number}
              </span>
              <span className="text-slate-600">•</span>
              <h1 className="text-sm font-semibold text-slate-100">{caseData.title}</h1>
              <StatusBadge status={caseData.status} />
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5 font-mono">
              <span>SEED:</span>
              <AddressDisplay address={caseData.reported_wallet_address} />
              <span>•</span>
              <span className="uppercase text-slate-300">{caseData.blockchain}</span>
              <span>•</span>
              <span className="text-amber-400">{caseData.fraud_type.replace('_', ' ')}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-[#121620] px-3 py-1.5 rounded border border-[#1F2637] text-xs font-mono text-slate-300">
            <span className="text-slate-400">HOPS:</span>
            <select
              value={maxHops}
              onChange={(e) => setMaxHops(Number(e.target.value))}
              className="bg-transparent text-blue-400 font-bold focus:outline-none cursor-pointer"
            >
              <option value={1} className="bg-[#121620]">1 Hop</option>
              <option value={2} className="bg-[#121620]">2 Hops</option>
              <option value={3} className="bg-[#121620]">3 Hops</option>
              <option value={4} className="bg-[#121620]">4 Hops</option>
              <option value={5} className="bg-[#121620]">5 Hops</option>
            </select>
          </div>

          <button
            onClick={handleExecuteTrace}
            disabled={traceMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold shadow-md transition-colors disabled:opacity-50 cursor-pointer"
          >
            {traceMutation.isPending ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Tracing...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Trace</span>
              </>
            )}
          </button>

          <button
            onClick={handleExportBrief}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#121620] hover:bg-slate-800 text-slate-300 border border-[#1F2637] rounded text-xs font-medium transition-colors cursor-pointer"
            title="Export Case Brief"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export Brief</span>
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden relative">
        <div className="flex-1 h-full relative">
          <FundFlowCanvas
            trace={currentTrace}
            isLoading={traceMutation.isPending}
          />
        </div>

        <InspectorDrawer />
      </div>

      <BottomDock />
    </div>
  );
};
