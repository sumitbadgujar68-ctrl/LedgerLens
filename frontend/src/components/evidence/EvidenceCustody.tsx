import React, { useState, useMemo } from 'react';
import { TopBar } from '../layout/TopBar';
import { useInvestigationStore } from '../../store/investigationStore';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { EvidenceItem } from '../../types';
import {
  Download,
  CheckCircle2,
  Lock,
  Search,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

interface SealedEvidenceRecord {
  id: string;
  type: string;
  caseRef: string;
  hash: string;
  timestamp: string;
  blockNumber: number;
  custodian: string;
  provenance: 'live' | 'ai' | 'analyst' | 'demo' | 'derived' | 'public_source';
  status: string;
  merkleLeaf: string;
  payload: Record<string, unknown>;
  rawEvidence?: EvidenceItem;
}

function mapEvidenceToRecord(evidence: EvidenceItem): SealedEvidenceRecord {
  const isDemo = evidence.demo_data;
  const findingSource = evidence.finding_source || '';
  
  let provenance: SealedEvidenceRecord['provenance'] = 'demo';
  if (findingSource === 'live_on_chain' || (evidence.evidence_type === 'wallet' && !isDemo)) {
    provenance = 'live';
  } else if (findingSource === 'synthetic_demo' || isDemo) {
    provenance = 'demo';
  } else if (evidence.evidence_type === 'pattern' && !isDemo) {
    provenance = 'derived';
  } else if (evidence.evidence_type === 'note') {
    provenance = 'analyst';
  }

  const typeLabels: Record<string, string> = {
    wallet: 'Wallet Trace Artifact',
    note: 'Investigator Note',
    pattern: 'Pattern Detection',
  };

  return {
    id: `EVD-${evidence.evidence_id.slice(0, 8).toUpperCase()}`,
    type: typeLabels[evidence.evidence_type] || evidence.evidence_type,
    caseRef: evidence.reference_id ? evidence.reference_id.slice(0, 16).toUpperCase() : 'N/A',
    hash: 'sha256:' + evidence.evidence_id.slice(0, 32),
    timestamp: new Date(evidence.pinned_at).toUTCString(),
    blockNumber: 0,
    custodian: 'LedgerLens System',
    provenance,
    status: 'SEALED & VERIFIED',
    merkleLeaf: '0x' + evidence.evidence_id.slice(0, 32),
    payload: {
      evidence_id: evidence.evidence_id,
      evidence_type: evidence.evidence_type,
      finding_source: evidence.finding_source,
      demo_data: evidence.demo_data,
      investigator_note: evidence.investigator_note,
      reference_id: evidence.reference_id,
    },
    rawEvidence: evidence,
  };
}

export const EvidenceCustody: React.FC = () => {
  const { currentCase, evidenceNotes, addEvidenceNote } = useInvestigationStore();
  const [activeFilter, setActiveFilter] = useState<'all' | 'live' | 'ai' | 'analyst' | 'demo' | 'derived' | 'public_source'>('all');
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [newNoteTag, setNewNoteTag] = useState<'lead' | 'custody' | 'subpoena'>('custody');

  const caseId = currentCase?.case_id;

  const { data: evidenceData, isLoading, error } = useQuery({
    queryKey: ['evidence', caseId],
    queryFn: () => api.getCaseEvidence(caseId!),
    enabled: !!caseId,
  });

  const apiRecords = useMemo(() => {
    if (!evidenceData?.evidence) return [];
    return evidenceData.evidence.map(mapEvidenceToRecord);
  }, [evidenceData]);

  const userRecords: SealedEvidenceRecord[] = useMemo(() => {
    return evidenceNotes.map((n, i) => ({
      id: `EVD-LOCAL-${Date.now()}-${i}`,
      type: 'Investigator Sworn Note',
      caseRef: n.caseId || caseId?.slice(0, 16).toUpperCase() || 'N/A',
      hash: 'sha256:' + n.content.slice(0, 32),
      timestamp: n.timestamp,
      blockNumber: 0,
      custodian: n.author || 'Det. K. Vance',
      provenance: 'analyst',
      status: 'LOCAL NOTE (NOT SEALED)',
      merkleLeaf: '0x' + n.content.slice(0, 32),
      payload: { content: n.content, tag: n.tag, local: true },
    }));
  }, [evidenceNotes, caseId]);

  const allRecords = [...userRecords, ...apiRecords];

  const filteredRecords = allRecords.filter((rec) => {
    const matchesFilter = activeFilter === 'all' || rec.provenance === activeFilter;
    const matchesSearch =
      rec.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rec.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rec.hash.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rec.custodian.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rec.caseRef.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const selectedRecord = selectedRecordId 
    ? allRecords.find((r) => r.id === selectedRecordId) || allRecords[0] 
    : allRecords[0];

  const provenanceCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    allRecords.forEach(r => { counts[r.provenance] = (counts[r.provenance] || 0) + 1; });
    return counts;
  }, [allRecords]);

  const handleExportSAR = () => {
    if (apiRecords.length === 0 && userRecords.length === 0) {
      alert('No evidence artifacts available to export for this case.');
      return;
    }
    const exportData = {
      case_id: caseId,
      exported_at: new Date().toISOString(),
      artifacts: allRecords.map(r => ({
        id: r.id,
        type: r.type,
        provenance: r.provenance,
        hash: r.hash,
        timestamp: r.timestamp,
        payload: r.payload,
      })),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `evidence-export-${caseId?.slice(0, 8)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleSaveNewNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteContent.trim()) return;
    addEvidenceNote({
      caseId: caseId || 'unknown',
      author: 'Det. K. Vance (LL-8491)',
      content: newNoteContent,
      tag: newNoteTag,
    });
    setNewNoteContent('');
    setIsNewModalOpen(false);
  };

  if (!caseId) {
    return (
      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] select-none">
        <TopBar />
        <main className="flex-1 flex items-center justify-center p-8">
          <div className="text-center text-[var(--color-on-surface-variant)]">
            <FileText className="w-16 h-16 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No case selected</p>
            <p className="text-sm mt-2">Open a case from the dashboard to view its evidence custody locker.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] select-none">
      <TopBar />

      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header Summary & Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[var(--color-outline)] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-wide text-[var(--color-on-surface)]">Evidence Custody Locker</h1>
                <span className="px-2 py-1 rounded bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/20 text-[10px] font-bold">
                  {apiRecords.length > 0 ? 'DIGEST & INTEGRITY VERIFIED' : 'NO SEALED ARTIFACTS'}
                </span>
              </div>
              <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">
                {apiRecords.length > 0 
                  ? `Hashed forensic artifacts from live trace data for case ${currentCase?.case_number}.`
                  : 'No sealed evidence artifacts exist for this case. Run a trace to generate on-chain evidence, or add analyst notes below.'}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsNewModalOpen(true)}
                type="button"
                className="inline-flex items-center gap-2 px-6 py-2 bg-[var(--accent-blue)] hover:bg-blue-600 rounded text-[11px] font-bold text-[var(--color-on-surface)] shadow-sm transition-colors uppercase"
                style={{ backgroundColor: '#3b82f6' }}
              >
                <span>+ SEAL NEW ANALYST NOTE</span>
              </button>

              <button
                onClick={handleExportSAR}
                type="button"
                className="inline-flex items-center gap-2 px-6 py-2 bg-[var(--color-surface-dim)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] rounded text-[11px] font-bold border border-[var(--color-outline)] transition-colors uppercase tracking-wider"
              >
                <Download className="w-4 h-4 text-[#3b82f6]" />
                <span>EXPORT EVIDENCE PACKAGE</span>
              </button>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-primary)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="text-[13px] text-[var(--color-on-surface-variant)] font-medium">Sealed On-Chain Artifacts</span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">{provenanceCounts.live || 0}</span>
                <span className="text-[11px] font-semibold text-[var(--color-secondary)]">LIVE ON-CHAIN</span>
              </div>
            </div>

            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-tertiary)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="text-[13px] text-[var(--color-on-surface-variant)] font-medium">Derived / Computed</span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">{provenanceCounts.derived || 0}</span>
                <span className="text-[11px] font-semibold text-[var(--color-tertiary)]">DERIVED</span>
              </div>
            </div>

            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-secondary)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="text-[13px] text-[var(--color-on-surface-variant)] font-medium">Demo / Synthetic</span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">{provenanceCounts.demo || 0}</span>
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)]">DEMO DATA</span>
              </div>
            </div>

            <div className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-on-surface-variant)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="text-[13px] text-[var(--color-on-surface-variant)] font-medium">Analyst Notes (Local)</span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-[var(--color-on-surface)]">{provenanceCounts.analyst || 0}</span>
                <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)]">LOCAL ONLY</span>
              </div>
            </div>
          </div>

          {/* Filter & Search */}
          <div className="bg-[var(--color-surface-container-low)] p-4 rounded-xl border border-[var(--color-outline)]/50 space-y-4">
            <div className="flex flex-col lg:flex-row gap-4 justify-between">
              <div className="flex items-center gap-1 bg-[var(--color-surface-dim)] p-1 rounded-lg border border-[var(--color-outline)] overflow-x-auto hide-scrollbar">
                <button
                  onClick={() => setActiveFilter('all')}
                  className={`px-4 py-1.5 text-[11px] font-semibold rounded-md transition-colors whitespace-nowrap tracking-wider uppercase ${
                    activeFilter === 'all'
                      ? 'bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] border-b-2 border-[var(--color-primary)]'
                      : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'
                  }`}
                >
                  ALL ({allRecords.length})
                </button>
                <button
                  onClick={() => setActiveFilter('live')}
                  className={`px-4 py-1.5 text-[11px] font-semibold rounded-md transition-colors whitespace-nowrap tracking-wider uppercase ${
                    activeFilter === 'live'
                      ? 'bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] border-b-2 border-[var(--color-primary)]'
                      : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'
                  }`}
                >
                  LIVE ON-CHAIN ({provenanceCounts.live || 0})
                </button>
                <button
                  onClick={() => setActiveFilter('derived')}
                  className={`px-4 py-1.5 text-[11px] font-semibold rounded-md transition-colors whitespace-nowrap tracking-wider uppercase ${
                    activeFilter === 'derived'
                      ? 'bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] border-b-2 border-[var(--color-primary)]'
                      : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'
                  }`}
                >
                  DERIVED ({provenanceCounts.derived || 0})
                </button>
                <button
                  onClick={() => setActiveFilter('analyst')}
                  className={`px-4 py-1.5 text-[11px] font-semibold rounded-md transition-colors whitespace-nowrap tracking-wider uppercase ${
                    activeFilter === 'analyst'
                      ? 'bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] border-b-2 border-[var(--color-primary)]'
                      : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'
                  }`}
                >
                  ANALYST INPUT ({provenanceCounts.analyst || 0})
                </button>
                <button
                  onClick={() => setActiveFilter('demo')}
                  className={`px-4 py-1.5 text-[11px] font-semibold rounded-md transition-colors whitespace-nowrap tracking-wider uppercase ${
                    activeFilter === 'demo'
                      ? 'bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] border-b-2 border-[var(--color-primary)]'
                      : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'
                  }`}
                >
                  DEMO DATA ({provenanceCounts.demo || 0})
                </button>
              </div>

              <div className="relative max-w-sm w-full">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-on-surface-variant)]" />
                <input
                  type="text"
                  placeholder="Search evidence ID, type, custodian, case ref..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-lg pl-9 pr-3 py-2 text-[13px] text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Loading / Error / Empty states */}
          {isLoading && (
            <div className="py-12 text-center text-sm text-[var(--color-on-surface-variant)] font-medium">
              Loading evidence artifacts...
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-950/20 rounded-xl border border-red-900/50 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[var(--color-error)] shrink-0" />
              <span className="text-[11px] font-bold text-red-400">Failed to load evidence: {(error as any)?.message || 'Unknown error'}</span>
            </div>
          )}

          {!isLoading && !error && filteredRecords.length === 0 && allRecords.length === 0 && (
            <div className="py-12 text-center text-sm text-[var(--color-on-surface-variant)] space-y-2">
              <FileText className="w-16 h-16 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No evidence artifacts found for this case.</p>
              <p className="text-xs">Run a trace to generate on-chain evidence, or add an analyst note below.</p>
            </div>
          )}

          {!isLoading && !error && filteredRecords.length === 0 && allRecords.length > 0 && (
            <div className="py-12 text-center text-sm text-[var(--color-on-surface-variant)] space-y-2">
              <Search className="w-16 h-16 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No artifacts match your current filters.</p>
              <p className="text-xs">Try adjusting the filter or search query.</p>
            </div>
          )}

          {/* Ledger Table + Inspector split */}
          {!isLoading && !error && (filteredRecords.length > 0 || allRecords.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Table */}
              <div className="lg:col-span-2 bg-[var(--color-surface-container-low)] border border-[var(--color-outline)]/50 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-[var(--color-outline)] flex items-center justify-between">
                  <span className="font-semibold text-[var(--color-on-surface)] uppercase text-[12px]">Forensic Evidence Ledger</span>
                  <span className="text-[12px] text-[var(--color-on-surface-variant)]">
                    {filteredRecords.length} OF {allRecords.length} ARTIFACTS
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider border-b border-[var(--color-outline)]">
                        <th className="py-4 px-6">ID</th>
                        <th className="py-4 px-6">TYPE</th>
                        <th className="py-4 px-6">CASE REF</th>
                        <th className="py-4 px-6">HASH</th>
                        <th className="py-4 px-6">PROVENANCE</th>
                        <th className="py-4 px-6">STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--color-outline)]">
                      {filteredRecords.map((r) => (
                        <tr
                          key={r.id}
                          onClick={() => setSelectedRecordId(r.id)}
                          className={`hover:bg-[var(--color-surface-container-high)] cursor-pointer transition-colors group ${
                            selectedRecordId === r.id ? 'bg-[var(--color-surface-container-high)] border-l-2 border-l-[var(--color-primary)]' : 'border-l-2 border-l-transparent'
                          }`}
                        >
                          <td className={`py-4 px-6 font-bold text-[13px] ${selectedRecordId === r.id ? 'text-[var(--color-primary)]' : 'text-[var(--color-on-surface)]'}`}>
                            {r.id}
                          </td>
                          <td className="py-4 px-6 text-[13px] text-[var(--color-on-surface)]">{r.type}</td>
                          <td className="py-4 px-6 text-[13px] text-[var(--color-on-surface-variant)]">{r.caseRef}</td>
                          <td className="py-4 px-6 text-[13px]">
                            <span className="font-bold text-[var(--color-on-surface-variant)]" title={r.hash}>
                              {r.hash.slice(0, 12)}...{r.hash.slice(-4)}
                            </span>
                          </td>
                          <td className="py-4 px-6">
                            <ProvenanceBadge variant={r.provenance} size="sm" />
                          </td>
                          <td className="py-4 px-6">
                            <span className={`inline-flex items-center gap-1.5 text-[10px] uppercase font-bold ${
                              r.provenance === 'live' ? 'text-[var(--color-secondary)]' :
                              r.provenance === 'derived' ? 'text-[var(--color-tertiary)]' :
                              r.provenance === 'demo' ? 'text-amber-400' :
                              r.provenance === 'analyst' ? 'text-[var(--color-on-surface-variant)]' :
                              'text-[var(--color-on-surface)]'
                            }`}>
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>{r.status}</span>
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Inspector */}
              {selectedRecord && (
                <div className="bg-[var(--color-surface-container-low)] border border-[var(--color-outline)]/50 rounded-xl p-5 space-y-5 h-fit">
                  <div className="flex items-center justify-between pb-3 border-b border-[var(--color-outline)]">
                    <div className="flex items-center gap-2">
                      <Lock className="w-4 h-4 text-[var(--color-primary)]" />
                      <span className="font-bold text-[var(--color-on-surface)] uppercase text-[12px]">
                        EVIDENCE INSPECTOR
                      </span>
                    </div>
                    <span className="text-[var(--color-primary)] font-bold text-[12px]">{selectedRecord.id}</span>
                  </div>

                  {/* Certificate */}
                  <div className="p-3 rounded-lg bg-[var(--color-secondary)]/10 border border-[var(--color-secondary)]/20 space-y-1">
                    <div className="flex items-center gap-1.5 text-[var(--color-secondary)] font-bold text-[11px] uppercase">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>
                        {selectedRecord.rawEvidence ? 'CRYPTOGRAPHIC CERTIFICATE VALID' : 'LOCAL NOTE - NOT CRYPTOGRAPHICALLY SEALED'}
                      </span>
                    </div>
                    <p className="text-[11px] text-[var(--color-secondary)]/80 leading-snug">
                      {selectedRecord.rawEvidence
                        ? 'SHA-256 digest verified against trace graph and blockchain records.'
                        : 'This note is stored locally and has not been sealed to the evidence locker.'}
                    </p>
                  </div>

                  {/* Metadata */}
                  <div className="p-4 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)] space-y-3 text-[12px]">
                    <div className="flex justify-between">
                      <span className="text-[var(--color-on-surface-variant)] font-medium">TIMESTAMP</span>
                      <span className="text-[var(--color-on-surface)] font-bold">{selectedRecord.timestamp}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--color-on-surface-variant)] font-medium">CUSTODIAN</span>
                      <span className="text-[var(--color-on-surface)] font-medium">{selectedRecord.custodian}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--color-on-surface-variant)] font-medium">PROVENANCE</span>
                      <ProvenanceBadge variant={selectedRecord.provenance} size="md" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--color-on-surface-variant)] font-medium">MERKLE LEAF</span>
                      <span className="text-[var(--color-primary)] font-bold truncate ml-4">{selectedRecord.merkleLeaf}</span>
                    </div>
                    {selectedRecord.rawEvidence && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-[var(--color-on-surface-variant)] font-medium">FINDING SOURCE</span>
                          <span className="text-[var(--color-on-surface)] font-bold">{selectedRecord.rawEvidence.finding_source}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--color-on-surface-variant)] font-medium">DEMO DATA FLAG</span>
                          <span className={`font-bold ${selectedRecord.rawEvidence.demo_data ? 'text-amber-400' : 'text-[var(--color-secondary)]'}`}>
                            {selectedRecord.rawEvidence.demo_data ? 'YES' : 'NO'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--color-on-surface-variant)] font-medium">EVIDENCE TYPE</span>
                          <span className="text-[var(--color-on-surface)] font-bold">{selectedRecord.rawEvidence.evidence_type}</span>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Raw JSON */}
                  <div className="space-y-2">
                    <span className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider">RAW ARTIFACT PAYLOAD</span>
                    <pre className="p-4 bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-lg text-[11px] text-blue-400 overflow-x-auto max-h-48 font-[Inter] font-medium">
                      {JSON.stringify(selectedRecord.payload, null, 2)}
                    </pre>
                  </div>

                  {/* Action */}
                  <div className="pt-4 border-t border-[var(--color-outline)]">
                    <button
                      type="button"
                      onClick={() => {
                        const blob = new Blob([JSON.stringify(selectedRecord.payload, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const anchor = document.createElement('a');
                        anchor.href = url;
                        anchor.download = `${selectedRecord.id}_payload.json`;
                        anchor.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-surface)] text-[13px] font-bold transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      <span>EXPORT ARTIFACT PAYLOAD</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* New Sealed Evidence Note Modal */}
      {isNewModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <form
            onSubmit={handleSaveNewNote}
            className="w-full max-w-md bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-2xl p-6 space-y-5 shadow-2xl"
          >
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-outline)]">
              <span className="font-bold text-[var(--color-on-surface)] text-lg">SEAL NEW ANALYST NOTE</span>
              <button
                type="button"
                onClick={() => setIsNewModalOpen(false)}
                className="text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-[12px] font-semibold text-[var(--color-on-surface-variant)] uppercase">OBSERVATION / NOTE CONTENT</label>
              <textarea
                value={newNoteContent}
                onChange={(e) => setNewNoteContent(e.target.value)}
                placeholder="Enter evidentiary findings, on-chain trace confirmation..."
                rows={4}
                required
                className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl p-3 text-[13px] text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] transition-colors placeholder:text-[var(--color-on-surface-variant)]"
              />
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-[12px] font-semibold text-[var(--color-on-surface-variant)] uppercase block mb-2">CLASSIFICATION TAG</label>
                <select
                  value={newNoteTag}
                  onChange={(e) => setNewNoteTag(e.target.value as any)}
                  className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-3 py-2.5 text-[13px] text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] transition-colors cursor-pointer"
                >
                  <option value="custody">CUSTODY TRANSFER</option>
                  <option value="lead">INVESTIGATIVE LEAD</option>
                  <option value="subpoena">SUBPOENA PACKAGING</option>
                </select>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsNewModalOpen(false)}
                  className="flex-1 py-2.5 rounded-xl bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] font-semibold border border-[var(--color-outline)] hover:bg-[var(--color-surface-container-high)] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl bg-[var(--color-primary)] text-[var(--color-on-surface)] font-bold hover:brightness-110 transition-colors"
                >
                  Seal & Save Locally
                </button>
              </div>
            </div>
            <p className="text-xs text-[var(--color-on-surface-variant)] text-center">
              Note: This saves locally only. No backend evidence creation endpoint exists yet.
            </p>
          </form>
        </div>
      )}
    </div>
  );
};