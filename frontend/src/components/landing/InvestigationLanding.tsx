import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { Case, CaseCreatePayload, BlockchainType } from '../../types';
import {
  Search,
  ArrowRight,
  Shield,
  Zap,
  AlertTriangle,
} from 'lucide-react';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

/* ──────────────────────────────────────────────────────────
 * Address / chain detection helpers
 * ────────────────────────────────────────────────────────── */

function isTxHash(input: string): boolean {
  return /^0x[a-fA-F0-9]{64}$/.test(input.trim());
}

function detectChain(input: string): BlockchainType | null {
  const trimmed = input.trim();
  // Ethereum wallet address (0x + 40 hex chars)
  if (/^0x[a-fA-F0-9]{40}$/.test(trimmed)) return 'ethereum';
  return null; // Bitcoin and Tron not supported in this MVP
}

function shortenAddress(addr: string): string {
  if (!addr) return '';
  if (addr.length <= 14) return addr;
  return `${addr.slice(0, 8)}…${addr.slice(-6)}`;
}

function chainColor(chain: string): string {
  switch (chain) {
    case 'ethereum': return '#627EEA';
    case 'bitcoin': return '#F7931A';
    case 'tron': return '#FF0013';
    default: return '#8B8FA3';
  }
}

function chainLabel(chain: string): string {
  switch (chain) {
    case 'ethereum': return 'ETHEREUM';
    case 'bitcoin': return 'BITCOIN';
    case 'tron': return 'TRON';
    default: return chain.toUpperCase();
  }
}

function fraudLabel(ft: string): string {
  return ft.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/* ──────────────────────────────────────────────────────────
 * InvestigationLanding
 * ────────────────────────────────────────────────────────── */

export const InvestigationLanding: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState('');
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Fetch ALL cases for display
  const { data: cases = [], isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.getCases(),
  });

  // Featured investigations: pick up to 5 with preference for canonical case and multi-chain diversity
  const featuredCases = React.useMemo(() => {
    if (!cases.length) return [];
    const picks: Case[] = [];
    const canonical = cases.find(c => c.case_number === 'CASE-2026-000001');
    if (canonical) {
      picks.push(canonical);
    }
    const ethCases = cases.filter(c => c.blockchain === 'ethereum' && c.case_id !== canonical?.case_id);
    if (ethCases[0]) picks.push(ethCases[0]);
    if (ethCases[1]) picks.push(ethCases[1]);
    
    // Fill remaining from whatever is left
    for (const c of cases) {
      if (picks.length >= 5) break;
      if (!picks.find(p => p.case_id === c.case_id)) picks.push(c);
    }
    return picks;
  }, [cases]);

  // Create case mutation
  const createMutation = useMutation({
    mutationFn: (payload: CaseCreatePayload) => api.createCase(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });

  // Handle search / investigate
  const handleInvestigate = useCallback(async () => {
    const input = searchInput.trim();
    if (!input) {
      setSearchError('Enter a wallet address, transaction hash, or case ID');
      return;
    }
    setSearchError(null);

    const matchCase = cases.find(
      c => c.case_id === input || c.reported_wallet_address.toLowerCase() === input.toLowerCase()
    );
    if (matchCase) {
      navigate(`/cases/${matchCase.case_id}`);
      return;
    }

    if (isTxHash(input)) {
      setSearchError('Transaction hash detected. Graph fund flow tracing requires an Ethereum wallet address (0x… 40 hex chars). Please enter the target wallet address.');
      return;
    }

    const chain = detectChain(input);
    if (!chain) {
      setSearchError('Invalid address format. Please enter a valid 40-character hexadecimal Ethereum wallet address (0x…).');
      return;
    }

    setIsCreating(true);
    try {
      // Step 1: Create the case docket
      const payload: CaseCreatePayload = {
        title: `${chainLabel(chain)} Investigation — ${shortenAddress(input)}`,
        reported_wallet_address: input,
        blockchain: chain,
        fraud_type: 'other',
        investigator_notes: `Live investigation started from LedgerLens landing page for ${chain} address ${input}`,
      };
      
      // Use API directly to avoid premature navigation from mutation side-effects
      const newCase = await api.createCase(payload);
      
      // Step 2: Immediately trigger the real on-chain trace
      setSearchError('Fetching real on-chain data... this may take up to 10 seconds.'); 
      try {
        await api.runTrace(newCase.case_id, {
          start_wallet_address: input,
          direction: 'outbound',
          max_hops: 1, // Keep it at 1 hop for initial fast load
          max_branches: 5
        });
      } catch (traceErr: any) {
        console.warn('Initial on-chain trace note:', traceErr);
      }

      // Step 3: Invalidate cache and transition to workspace
      queryClient.invalidateQueries({ queryKey: ['cases'] });
      navigate(`/cases/${newCase.case_id}`);
      
    } catch (err: any) {
      setSearchError(err?.message || 'Failed to initialize investigation from blockchain data');
    } finally {
      setIsCreating(false);
    }
  }, [searchInput, cases, navigate, queryClient]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleInvestigate();
  };

  // Open existing case
  const openCase = (caseId: string) => {
    navigate(`/cases/${caseId}`);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-auto bg-[var(--color-surface-dim)] text-[var(--color-on-surface)]">

      <div className="px-8 pt-8 pb-4">
        <h1 className="text-2xl font-bold font-[Inter] tracking-tight text-[var(--color-on-surface)] mb-8">
          Dashboard
        </h1>
        
        {/* Stats Row */}
        <div className="flex gap-4 mb-8">
          <div className="w-48 flex flex-col justify-between">
            <div>
              <div className="text-[13px] text-[var(--color-on-surface-variant)] mb-1">Total Investigations</div>
              <div className="text-[28px] font-bold text-[var(--color-on-surface)]">{cases.length}</div>
            </div>
            <div className="h-1 w-full bg-[var(--color-primary)] rounded-full mt-2"></div>
          </div>
          <div className="w-48 flex flex-col justify-between">
            <div>
              <div className="text-[13px] text-[var(--color-on-surface-variant)] mb-1">Active Cases</div>
              <div className="text-[28px] font-bold text-[var(--color-on-surface)]">{cases.filter(c => c.status === 'active').length}</div>
            </div>
            <div className="h-1 w-full bg-[#627EEA] rounded-full mt-2"></div>
          </div>
          <div className="w-48 flex flex-col justify-between">
            <div>
              <div className="text-[13px] text-[var(--color-on-surface-variant)] mb-1">Archived</div>
              <div className="text-[28px] font-bold text-[var(--color-on-surface)]">{cases.filter(c => c.status === 'archived').length}</div>
            </div>
            <div className="h-1 w-full bg-[var(--color-outline)] rounded-full mt-2"></div>
          </div>
        </div>

        {/* ── Search Bar Card ── */}
        <div className="w-full max-w-3xl bg-[var(--color-surface-container)] rounded-2xl p-6 border border-transparent">
          <div className="text-[14px] font-semibold mb-4 text-[var(--color-on-surface)]">Start New Investigation</div>
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-on-surface-variant)]/60" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => { setSearchInput(e.target.value); setSearchError(null); }}
                onKeyDown={handleKeyDown}
                placeholder="Paste wallet address, transaction hash, or case ID..."
                className="w-full pl-12 pr-4 py-3.5 bg-[var(--color-surface-container)] border border-[var(--color-outline)]/60 rounded-xl text-[15px] text-[var(--color-on-surface)] placeholder:text-[var(--color-on-surface-variant)]/50 focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)]/30 transition-all"
              />
              {searchInput && detectChain(searchInput) && (
                <span
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono font-bold px-2 py-0.5 rounded"
                  style={{
                    color: chainColor(detectChain(searchInput)!),
                    backgroundColor: `${chainColor(detectChain(searchInput)!)}20`,
                    border: `1px solid ${chainColor(detectChain(searchInput)!)}40`
                  }}
                >
                  {chainLabel(detectChain(searchInput)!)}
                </span>
              )}
            </div>
            <button
              onClick={handleInvestigate}
              disabled={isCreating || createMutation.isPending}
              className="px-6 py-3.5 bg-[var(--color-primary)] text-[var(--color-on-primary)] rounded-xl font-semibold text-[14px] hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              {isCreating ? (
                <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              Investigate
            </button>
          </div>
          {searchError && (
            <div className="mt-2 flex items-center gap-2 text-[13px] text-[var(--color-error)]">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {searchError}
            </div>
          )}
        </div>
      </div>

      {/* ── Featured Investigations ── */}
      <div className="px-8 py-4 flex-1">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-[16px] font-bold text-[var(--color-on-surface)] font-[Inter]">
              Recent Investigations
            </h2>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="h-44 rounded-xl bg-[var(--color-surface-container)] animate-pulse" />
            ))}
          </div>
        ) : featuredCases.length === 0 ? (
          <div className="text-center py-16 text-[var(--color-on-surface-variant)]">
            <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-[15px] font-medium">No investigations yet</p>
            <p className="text-[13px] mt-1">Paste a wallet address above to start your first investigation</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {featuredCases.map((c) => (
              <div
                key={c.case_id}
                onClick={() => openCase(c.case_id)}
                className="group text-left bg-[var(--color-surface-container)] rounded-2xl p-5 hover:bg-[var(--color-surface-bright)] transition-all duration-200 cursor-pointer relative overflow-hidden flex flex-col justify-between"
              >

                <div>
                  {/* Chain badge & status */}
                  <div className="flex items-center justify-between mb-3 mt-1">
                    <span
                      className="text-[10px] font-mono font-bold tracking-[0.1em] px-2 py-0.5 rounded"
                      style={{
                        color: chainColor(c.blockchain),
                        backgroundColor: `${chainColor(c.blockchain)}15`,
                        border: `1px solid ${chainColor(c.blockchain)}30`
                      }}
                    >
                      {chainLabel(c.blockchain)}
                    </span>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded text-[var(--color-secondary)] bg-[var(--color-secondary)]/10 border border-[var(--color-secondary)]/20 uppercase">
                      {c.status.replace(/_/g, ' ')}
                    </span>
                  </div>

                  {/* Address */}
                  <div className="font-mono text-[14px] text-[var(--color-on-surface)] font-semibold mb-1 break-all">
                    {shortenAddress(c.reported_wallet_address)}
                  </div>

                  {/* Title */}
                  <div className="text-[13px] text-[var(--color-on-surface-variant)] mb-3 line-clamp-2">
                    {c.title}
                  </div>

                  {/* Forensic Characteristics */}
                  <div className="space-y-1 mb-4 text-[11px] font-mono text-[var(--color-on-surface-variant)]/80 bg-[var(--color-surface-dim)]/50 p-2.5 rounded-lg border border-[var(--color-outline)]/20">
                    <div className="flex justify-between items-center">
                      <span>Typology:</span>
                      <span className="font-semibold text-[var(--color-on-surface)]">{fraudLabel(c.fraud_type)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Trace Depth:</span>
                      {c.blockchain === 'ethereum' ? (
                        <span className="text-[var(--color-primary)] font-semibold">Multi-Hop Graph (Active)</span>
                      ) : (
                        <span className="text-[var(--color-error)] font-semibold">ETH Only — Not Traced</span>
                      )}
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Provenance:</span>
                      <ProvenanceBadge variant={c.demo_data ? 'demo' : 'live'} size="sm" />
                    </div>
                  </div>
                </div>

                {/* Open Button Action */}
                <div className="pt-2 border-t border-[var(--color-outline)]/20 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[var(--color-on-surface-variant)]/60">
                    {c.case_number}
                  </span>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--color-primary)]/10 group-hover:bg-[var(--color-primary)] text-[var(--color-primary)] group-hover:text-[var(--color-on-primary)] text-xs font-bold transition-all"
                  >
                    <span>OPEN INVESTIGATION</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* All cases link */}
        {cases.length > 5 && (
          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/cases')}
              className="text-[13px] text-[var(--color-primary)] hover:underline font-semibold cursor-pointer"
            >
              View all {cases.length} investigations →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

