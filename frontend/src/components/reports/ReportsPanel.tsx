import React, { useState, useEffect, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { getToken } from '../../services/auth';
import type { GeneratedReport, ReportFormat, ReportType } from '../../types';
import {
  Download,
  FileText,
  ShieldCheck,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

interface ReportsPanelProps {
  caseId: string;
}

interface ReportSection {
  key: string;
  title: string;
  available: boolean;
  data: any;
  reason?: string;
  note?: string;
}

interface ReportData {
  case_id: string;
  case_number: string;
  title: string;
  report_type: string;
  format: string;
  generated_at: string;
  generated_by: string | null;
  sections: ReportSection[];
  unavailable_sections: string[];
}

const SECTION_RENDERERS: Record<string, (section: ReportSection) => React.ReactNode> = {
  case_information: (section) => {
    const d = section.data || {};
    return (
      <div className="space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Case ID:</span> <span className="font-mono text-[var(--color-on-surface)]">{d.case_id}</span></div>
          <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Case Number:</span> <span className="font-bold text-[var(--color-on-surface)]">{d.case_number}</span></div>
          <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Title:</span> <span className="text-[var(--color-on-surface)]">{d.title}</span></div>
          <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Blockchain:</span> <span className="text-[var(--color-primary)] font-bold uppercase">{d.blockchain}</span></div>
          <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Fraud Type:</span> <span className="text-[var(--color-on-surface)] capitalize">{d.fraud_type?.replace(/_/g, ' ')}</span></div>
          <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Status:</span> <span className="text-[var(--color-on-surface)] capitalize">{d.status?.replace(/_/g, ' ')}</span></div>
          {d.reported_amount && (
            <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Reported Amount:</span> <span className="text-[var(--color-primary)] font-bold">{d.reported_amount} {d.reported_asset || ''}</span></div>
          )}
          {d.reported_date && (
            <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Reported Date:</span> <span className="text-[var(--color-on-surface)]">{new Date(d.reported_date).toLocaleDateString()}</span></div>
          )}
        </div>
      </div>
    );
  },
  initial_reported_wallet: (section) => {
    const d = section.data || {};
    return (
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-[var(--color-on-surface-variant)] font-semibold">Wallet Address:</span>
          <span className="font-mono text-[var(--color-on-surface)] font-bold">{d.wallet_address}</span>
        </div>
        {d.reported_transaction_hash && (
          <div className="flex items-center gap-2">
            <span className="text-[var(--color-on-surface-variant)] font-semibold">Transaction Hash:</span>
            <span className="font-mono text-[var(--color-on-surface)]">{d.reported_transaction_hash}</span>
          </div>
        )}
      </div>
    );
  },
  investigation_methodology: (section) => {
    const d = section.data || {};
    return (
      <div className="space-y-2 text-sm">
        <p className="text-[var(--color-on-surface)] leading-relaxed">{d.description}</p>
        {d.trace_runs && d.trace_runs.length > 0 && (
          <div className="grid grid-cols-2 gap-3 text-xs mt-2">
            {d.trace_runs.map((r: any, i: number) => (
              <div key={i} className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
                <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Trace ID:</span> <span className="font-mono text-[var(--color-on-surface)]">{r.trace_id?.slice(0, 16)}...</span></div>
                <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Direction:</span> <span className="text-[var(--color-on-surface)] capitalize">{r.direction}</span></div>
                <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Max Hops:</span> <span className="text-[var(--color-on-surface)]">{r.max_hops}</span></div>
                <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Max Branches:</span> <span className="text-[var(--color-on-surface)]">{r.max_branches}</span></div>
                <div><span className="text-[var(--color-on-surface-variant)] font-semibold">Status:</span> <span className="text-[var(--color-secondary)] font-bold">{r.result_status || r.status}</span></div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  },
  transaction_timeline: (section) => {
    const d = section.data || {};
    return (
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-[var(--color-on-surface-variant)] font-semibold">Total Transactions:</span>
          <span className="text-[var(--color-primary)] font-bold">{d.count}</span>
          {d.complete ? (
            <span className="text-[var(--color-secondary)] text-xs font-bold px-2 py-0.5 rounded bg-[var(--color-secondary)]/10">Complete</span>
          ) : (
            <span className="text-[var(--color-tertiary)] text-xs font-bold px-2 py-0.5 rounded bg-[var(--color-tertiary)]/10">Truncated</span>
          )}
        </div>
        {d.note && <p className="text-[var(--color-on-surface-variant)] text-xs font-medium">{d.note}</p>}
        {d.transactions && d.transactions.length > 0 && (
          <div className="max-h-64 overflow-y-auto space-y-1">
            {d.transactions.slice(0, 10).map((t: any, i: number) => (
              <div key={i} className="p-2 bg-[var(--color-surface-dim)] rounded border border-[var(--color-outline)] text-xs font-mono">
                <div className="flex justify-between">
                  <span>{t.block_timestamp ? new Date(t.block_timestamp).toLocaleString() : 'N/A'}</span>
                  <span className="text-[var(--color-primary)]">{t.asset_symbol || 'ETH'} {t.amount}</span>
                </div>
                <div className="text-[var(--color-on-surface-variant)]">
                  {t.from_address?.slice(0, 10)}... → {t.to_address?.slice(0, 10)}...
                </div>
              </div>
            ))}
            {d.transactions.length > 10 && (
              <p className="text-[var(--color-on-surface-variant)] text-xs text-center">+ {d.transactions.length - 10} more transactions</p>
            )}
          </div>
        )}
      </div>
    );
  },
  graph_summary: (section) => {
    const d = section.data || {};
    return (
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
          <span className="text-[var(--color-on-surface-variant)] font-semibold block">Nodes</span>
          <span className="text-2xl font-bold text-[var(--color-primary)]">{d.node_count || 0}</span>
        </div>
        <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
          <span className="text-[var(--color-on-surface-variant)] font-semibold block">Edges</span>
          <span className="text-2xl font-bold text-[var(--color-secondary)]">{d.edge_count || 0}</span>
        </div>
        <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
          <span className="text-[var(--color-on-surface-variant)] font-semibold block">Max Hop Depth</span>
          <span className="text-2xl font-bold text-[var(--color-tertiary)]">{d.max_hop_depth || 0}</span>
        </div>
        <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
          <span className="text-[var(--color-on-surface-variant)] font-semibold block">Root Wallet</span>
          <span className="font-mono text-[var(--color-on-surface)] text-xs">{d.root_wallet_address?.slice(0, 10)}...{d.root_wallet_address?.slice(-6)}</span>
        </div>
      </div>
    );
  },
  intermediary_wallets: (section) => {
    const d = section.data || {};
    if (!d.wallets || d.wallets.length === 0) {
      return <p className="text-[var(--color-on-surface-variant)] text-sm">{section.note || 'No intermediary wallets identified'}</p>;
    }
    return (
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--color-on-surface)]">{d.count} intermediary wallet(s) identified</p>
        <div className="max-h-48 overflow-y-auto space-y-1">
          {d.wallets.slice(0, 10).map((w: any, i: number) => (
            <div key={i} className="p-2 bg-[var(--color-surface-dim)] rounded border border-[var(--color-outline)] text-xs">
              <div className="flex justify-between">
                <span className="font-mono">{w.address.slice(0, 10)}...{w.address.slice(-6)}</span>
                <span className="text-[var(--color-primary)]">Hop {w.first_seen_hop ?? '?'}</span>
              </div>
              <div className="text-[var(--color-on-surface-variant)]">Received: {w.received_count} | Sent: {w.sent_count}</div>
            </div>
          ))}
        </div>
      </div>
    );
  },
  destination_entities: (section) => {
    const d = section.data || {};
    if (!d.entities || d.entities.length === 0) {
      return <p className="text-[var(--color-on-surface-variant)] text-sm">{section.note || 'No destination entities identified'}</p>;
    }
    return (
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--color-on-surface)]">{d.count} destination address(es) identified</p>
        <div className="max-h-48 overflow-y-auto space-y-1">
          {d.entities.slice(0, 10).map((e: any, i: number) => (
            <div key={i} className="p-2 bg-[var(--color-surface-dim)] rounded border border-[var(--color-outline)] text-xs">
              <div className="flex justify-between items-center">
                <span className="font-mono">{e.address.slice(0, 10)}...{e.address.slice(-6)}</span>
                <span className="text-[var(--color-secondary)] font-bold">{e.received_count} txs</span>
              </div>
              <div className="text-[var(--color-on-surface-variant)]">
                {Object.entries(e.received_by_asset || {}).map(([asset, amount]) => (
                  <span key={asset} className="mr-2">{String(amount)} {asset}</span>
                ))}
              </div>
              {e.entity && (
                <div className="text-[var(--color-tertiary)] font-medium mt-1">
                  Attributed: {e.entity.entity_name} ({e.provenance_level}, {Math.round((e.confidence || 0) * 100)}%)
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  },
  vasp_attribution_results: (section) => {
    const d = section.data || {};
    if (!d.attributions || d.attributions.length === 0) {
      return <p className="text-[var(--color-on-surface-variant)] text-sm">{section.note || 'No VASP/entity attributions recorded'}</p>;
    }
    return (
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--color-on-surface)]">{d.count} attribution(s)</p>
        <div className="space-y-2">
          {d.attributions.map((a: any, i: number) => (
            <div key={i} className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-mono text-[var(--color-on-surface)]">{a.wallet_address?.slice(0, 10)}...{a.wallet_address?.slice(-6)}</div>
                  <div className="text-[var(--color-on-surface-variant)] text-xs">{a.attribution_method}</div>
                </div>
                <div className="text-right">
                  <span className="text-[var(--color-tertiary)] font-bold">{typeof a.entity === 'object' ? (a.entity?.name || a.entity?.entity_name) : a.entity}</span>
                  <div className="text-xs text-[var(--color-on-surface-variant)]">{a.provenance_level} · {Math.round((a.confidence || 0) * 100)}%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  },
  risk_analysis: (section) => {
    const d = section.data || {};
    if (!d.risk_scores || d.risk_scores.length === 0) {
      return <p className="text-[var(--color-on-surface-variant)] text-sm">{section.note || 'No risk scores calculated'}</p>;
    }
    const avgScore = d.risk_scores.reduce((a: number, r: any) => a + (r.score || 0), 0) / d.risk_scores.length;
    const highRisk = d.risk_scores.filter((r: any) => (r.score || 0) >= 70).length;
    const medRisk = d.risk_scores.filter((r: any) => (r.score || 0) >= 40 && (r.score || 0) < 70).length;
    const lowRisk = d.risk_scores.filter((r: any) => (r.score || 0) < 40).length;
    return (
      <div className="space-y-3">
        <div className="grid grid-cols-4 gap-3 text-sm">
          <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)] text-center">
            <span className="text-[var(--color-on-surface-variant)] font-semibold block">Avg Score</span>
            <span className="text-2xl font-bold text-[var(--color-primary)]">{Math.round(avgScore)}</span>
          </div>
          <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)] text-center">
            <span className="text-[var(--color-on-surface-variant)] font-semibold block">High (≥70)</span>
            <span className="text-xl font-bold text-[var(--color-error)]">{highRisk}</span>
          </div>
          <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)] text-center">
            <span className="text-[var(--color-on-surface-variant)] font-semibold block">Medium (40-69)</span>
            <span className="text-xl font-bold text-[var(--color-tertiary)]">{medRisk}</span>
          </div>
<div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)] text-center">
            <span className="text-[var(--color-on-surface-variant)] font-semibold block">{'Low (<40)'}</span>
            <span className="text-xl font-bold text-[var(--color-secondary)]">{lowRisk}</span>
          </div>
        </div>
        <div className="max-h-48 overflow-y-auto space-y-1 text-xs">
          {d.risk_scores.slice(0, 10).map((r: any, i: number) => (
            <div key={i} className="flex justify-between items-center p-2 bg-[var(--color-surface-dim)] rounded border border-[var(--color-outline)]">
              <span className="font-mono">{r.wallet_address?.slice(0, 10)}...{r.wallet_address?.slice(-6)}</span>
              <span className={`font-bold ${r.score >= 70 ? 'text-[var(--color-error)]' : r.score >= 40 ? 'text-[var(--color-tertiary)]' : 'text-[var(--color-secondary)]'}`}>
                {r.score} ({r.risk_category})
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  },
  detected_patterns: (section) => {
    const d = section.data || {};
    if (!d.patterns || d.patterns.length === 0) {
      return <p className="text-[var(--color-on-surface-variant)] text-sm">{section.note || 'No patterns detected'}</p>;
    }
    return (
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--color-on-surface)]">{d.count} pattern(s) detected</p>
        <div className="space-y-2">
          {d.patterns.map((p: any, i: number) => (
            <div key={i} className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
              <div className="flex justify-between">
                <span className="font-bold text-[var(--color-on-surface)] capitalize">{p.pattern_type?.replace(/_/g, ' ')}</span>
                <span className="text-[var(--color-primary)] font-bold">{Math.round((p.confidence || 0) * 100)}%</span>
              </div>
              <p className="text-[var(--color-on-surface-variant)] text-sm mt-1">{p.description}</p>
              <div className="text-xs text-[var(--color-on-surface-variant)] mt-1">Wallet: {p.wallet_address?.slice(0, 10)}...{p.wallet_address?.slice(-6)}</div>
            </div>
          ))}
        </div>
      </div>
    );
  },
  evidence_references: (section) => {
    const d = section.data || {};
    if (!d.evidence || d.evidence.length === 0) {
      return <p className="text-[var(--color-on-surface-variant)] text-sm">{section.note || 'No evidence references'}</p>;
    }
    return (
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--color-on-surface)]">{d.count} evidence item(s)</p>
        <div className="space-y-2">
          {d.evidence.map((e: any, i: number) => (
            <div key={i} className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
              <div className="flex justify-between">
                <span className="font-bold text-[var(--color-on-surface)]">{e.evidence_type}</span>
                <span className="text-[var(--color-on-surface-variant)] text-xs">{new Date(e.pinned_at).toLocaleDateString()}</span>
              </div>
              {e.investigator_note && <p className="text-sm text-[var(--color-on-surface)] mt-1">{e.investigator_note}</p>}
            </div>
          ))}
        </div>
      </div>
    );
  },
  investigator_notes: (section) => {
    const d = section.data || {};
    return (
      <div className="p-4 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
        <p className="text-[var(--color-on-surface)] whitespace-pre-wrap text-sm">{d.case_notes || 'No notes recorded'}</p>
      </div>
    );
  },
  limitations_and_disclaimers: (section) => {
    const d = section.data || {};
    return (
      <ul className="space-y-2 text-sm text-[var(--color-on-surface-variant)]">
        {(d.disclaimers || []).map((disc: string, i: number) => (
          <li key={i} className="flex gap-2">
            <span className="text-[var(--color-primary)]">›</span>
            <span>{disc}</span>
          </li>
        ))}
      </ul>
    );
  },
  generated_timestamp: (section) => {
    const d = section.data || {};
    return (
      <p className="text-[var(--color-on-surface-variant)] text-sm font-bold">
        Generated: {d.generated_at ? new Date(d.generated_at).toLocaleString() : 'Unknown'}
      </p>
    );
  },
};

function renderUnavailableSection(section: ReportSection) {
  return (
    <div className="p-4 bg-[var(--color-surface-dim)]/50 rounded-lg border border-[var(--color-outline)]/50 text-center text-sm text-[var(--color-on-surface-variant)]">
      <AlertCircle className="w-4 h-4 mx-auto mb-2 opacity-50" />
      <p className="font-medium">{section.reason || 'Data unavailable'}</p>
      {section.note && <p className="text-xs mt-1">{section.note}</p>}
    </div>
  );
}

export const ReportsPanel: React.FC<ReportsPanelProps> = ({ caseId }) => {
  const queryClient = useQueryClient();
  const [reportType, setReportType] = useState<ReportType>('detailed');
  const [format, setFormat] = useState<ReportFormat>('html');
  const [queuedNotice, setQueuedNotice] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [previewReport, setPreviewReport] = useState<ReportData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['reports', caseId],
    queryFn: () => api.listReports(caseId),
    enabled: !!caseId,
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateReport(caseId, { report_type: reportType, format }),
    onSuccess: (job) => {
      setQueuedNotice(`Dossier #${job.job_id.slice(0, 8)} ${job.status}: Dossier package compiled.`);
      queryClient.invalidateQueries({ queryKey: ['reports', caseId] });
      setTimeout(() => setQueuedNotice(null), 5000);
    },
    onError: (err: any) => {
      setQueuedNotice(`Compilation notice: ${err?.message || 'Failed to compile dossier'}`);
      setTimeout(() => setQueuedNotice(null), 7000);
    },
  });

  const handleDownload = async (report: GeneratedReport) => {
    try {
      const token = getToken();
      const response = await fetch(report.file_url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error('Download request failed');
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${report.report_type}_report_${caseId.slice(0, 8)}.${report.format}`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
    } catch {
      alert('Unable to download report file directly.');
    }
  };

  const fetchPreviewReport = async (reportId: string) => {
    setPreviewLoading(true);
    try {
      const token = getToken();
      const response = await fetch(`/api/v1/reports/${reportId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error('Failed to fetch report');
      }
      const data = await response.json();
      setPreviewReport(data);
    } catch (err) {
      console.error('Failed to load report preview:', err);
      setPreviewReport(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Auto-select the latest report for preview
  const latestReport = useMemo(() => {
    if (!data?.reports?.length) return null;
    return data.reports[0]; // Already sorted newest first
  }, [data?.reports]);

  useEffect(() => {
    if (latestReport) {
      setSelectedReportId(latestReport.report_id);
      fetchPreviewReport(latestReport.report_id);
    } else {
      setSelectedReportId(null);
      setPreviewReport(null);
    }
  }, [latestReport]);

  const reports = data?.reports || [];

  return (
    <div className="flex flex-col h-full bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] select-none">
      {/* Header & Generator Toolbar - Fixed at the top */}
      <div className="shrink-0 bg-[var(--color-surface-container-low)] border-b border-[var(--color-outline)] p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 z-10">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-[var(--color-primary)]" />
            <h2 className="text-sm font-bold text-[var(--color-on-surface)] uppercase tracking-wide">
              Forensic Dossier & Court Submission Generator
            </h2>
          </div>
          <p className="text-xs text-[var(--color-on-surface-variant)] mt-1">
            Compile cryptographically verifiable law enforcement SAR packages and judicial evidence dossiers.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value as ReportType)}
            className="bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-3 py-2 text-xs text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] cursor-pointer transition-colors"
          >
            <option value="detailed">Executive & Technical Dossier</option>
            <option value="summary">High-Level Executive Brief</option>
            <option value="evidence_export">Court Evidence Export (JSON-LD)</option>
          </select>

          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as ReportFormat)}
            className="bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-3 py-2 text-xs text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] cursor-pointer transition-colors"
          >
            <option value="pdf">PDF Dossier</option>
            <option value="json">JSON Metadata</option>
            <option value="html">HTML Bundle</option>
          </select>

          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            type="button"
            className="px-5 py-2 bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-surface)] rounded-xl text-xs font-bold transition-colors cursor-pointer disabled:opacity-50"
          >
            {generateMutation.isPending ? 'COMPILING...' : 'GENERATE DOSSIER'}
          </button>
        </div>
      </div>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {queuedNotice && (
          <div className="p-3 rounded-xl bg-[var(--color-secondary)]/10 border border-[var(--color-secondary)]/20 text-[var(--color-secondary)] text-xs font-bold flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            <span>{queuedNotice}</span>
          </div>
        )}

        {/* Main Grid: Document Preview + Existing Reports History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Official Case Report Document Preview */}
        <div className="lg:col-span-2 bg-[var(--color-surface-container-low)] border border-[var(--color-outline)]/50 rounded-2xl p-8 shadow-xl relative overflow-hidden space-y-6">
          {/* Top Confidential Watermark Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[var(--color-outline)] text-[11px] font-bold">
            <span className="px-3 py-1 rounded-md bg-[var(--color-error)]/10 text-[var(--color-error)] font-bold border border-red-500/20">
              CONFIDENTIAL // LAW ENFORCEMENT & COMPLIANCE
            </span>
            <span className="text-[var(--color-on-surface-variant)] font-semibold">CASE REF: {caseId.slice(0, 16)}</span>
          </div>

          {/* Document Title */}
          <div>
            <div className="text-[11px] font-bold text-[var(--color-primary)] uppercase tracking-widest">
              LedgerLens Digital Forensics Division
            </div>
            <h1 className="text-xl font-bold text-[var(--color-on-surface)] tracking-tight mt-1">
              FORENSIC INVESTIGATION REPORT & FUND-FLOW AUDIT
            </h1>
            <div className="text-xs text-[var(--color-on-surface-variant)] mt-1.5 flex items-center gap-2">
              <span>Auto-generated from case data</span>
              <span>·</span>
              <span>Report Type: <span className="text-[var(--color-on-surface)] font-bold uppercase">{reportType}</span></span>
            </div>
          </div>

          {previewLoading ? (
            <div className="flex items-center justify-center py-12 text-sm text-[var(--color-on-surface-variant)]">
              <div className="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mr-3" />
              Loading report preview...
            </div>
          ) : previewReport ? (
            <>
              {previewReport.sections.map((section) => (
                <div key={section.key} className="space-y-2 pt-4 border-t border-[var(--color-outline)]">
                  <h3 className="text-[11px] font-bold text-[var(--color-on-surface-variant)] uppercase tracking-wider flex items-center gap-2">
                    {section.title}
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      section.available
                        ? 'bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/30'
                        : 'bg-[var(--color-error)]/10 text-[var(--color-error)] border border-[var(--color-error)]/30'
                    }`}>
                      {section.available ? 'AVAILABLE' : 'UNAVAILABLE'}
                    </span>
                  </h3>
                  {section.available
                    ? (SECTION_RENDERERS[section.key] ? SECTION_RENDERERS[section.key](section) : (
                        <pre className="p-3 bg-[var(--color-surface-dim)] rounded border border-[var(--color-outline)] text-xs overflow-auto max-h-64">
                          {JSON.stringify(section.data, null, 2)}
                        </pre>
                      ))
                    : renderUnavailableSection(section)}
                </div>
              ))}

              {/* Provenance Footer */}
              <div className="pt-4 border-t border-[var(--color-outline)] flex items-center justify-between text-xs text-[var(--color-on-surface-variant)] font-semibold">
                <div className="flex gap-2">
                  <ProvenanceBadge variant="live" size="sm" />
                  {previewReport.sections.some(s => s.key === 'risk_analysis' && s.available) && (
                    <ProvenanceBadge variant="derived" size="sm" />
                  )}
                  {previewReport.sections.some(s => s.key === 'detected_patterns' && s.available && s.data?.count > 0) && (
                    <ProvenanceBadge variant="derived" size="sm" />
                  )}
                  {previewReport.sections.some(s => s.key === 'vasp_attribution_results' && s.available && s.data?.count > 0) && (
                    <ProvenanceBadge variant="live" size="sm" />
                  )}
                  <ProvenanceBadge variant="analyst" size="sm" />
                </div>
                <span className="uppercase tracking-wider">
                  Evidentiary Archive Seal #LL-{caseId.slice(0, 6).toUpperCase()}
                </span>
              </div>
            </>
          ) : reports.length === 0 ? (
            <div className="py-12 text-center text-sm text-[var(--color-on-surface-variant)] space-y-2">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No compiled reports on file.</p>
              <p className="text-xs">Use the toolbar above to generate a new case dossier.</p>
            </div>
          ) : (
            <div className="py-12 text-center text-sm text-[var(--color-on-surface-variant)] space-y-2">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="font-medium">Select a report from the archive to preview.</p>
            </div>
          )}
        </div>

        {/* Right Col: Compiled Report Archive */}
        <div className="bg-[var(--color-surface-container-low)] border border-[var(--color-outline)]/50 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--color-outline)]">
            <span className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider">Compiled Dossiers</span>
            <span className="text-xs text-[var(--color-on-surface-variant)] font-bold">({reports.length})</span>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-sm text-[var(--color-on-surface-variant)] font-medium">Loading generated reports...</div>
          ) : reports.length === 0 ? (
            <div className="py-12 text-center text-sm text-[var(--color-on-surface-variant)] space-y-2">
              <p className="font-medium">No compiled reports on file.</p>
              <p className="text-xs">Use the toolbar above to generate a new case dossier.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((rep) => (
                <div
                  key={rep.report_id}
                  onClick={() => {
                    setSelectedReportId(rep.report_id);
                    fetchPreviewReport(rep.report_id);
                  }}
                  className={`p-4 bg-[var(--color-surface-dim)] rounded-xl border transition-colors cursor-pointer ${
                    selectedReportId === rep.report_id
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5'
                      : 'border-[var(--color-outline)] hover:border-[var(--color-primary)]/50'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[var(--color-primary)] uppercase tracking-wider">{rep.report_type}</span>
                    <span className="px-2 py-0.5 rounded-md bg-[var(--color-surface-container-low)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)] uppercase font-bold">
                      {rep.format}
                    </span>
                  </div>
                  <div className="text-[11px] text-[var(--color-on-surface-variant)] font-medium">
                    Generated: {new Date(rep.generated_at).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(rep);
                      }}
                      type="button"
                      className="flex items-center gap-2 py-1.5 px-3 rounded-lg bg-[var(--color-surface-container-low)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface)] text-xs font-bold border border-[var(--color-outline)] transition-colors cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5 text-[var(--color-primary)]" />
                      <span>Download {rep.format.toUpperCase()}</span>
                    </button>
                    {selectedReportId === rep.report_id && (
                      <CheckCircle className="w-5 h-5 text-[var(--color-primary)]" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
};