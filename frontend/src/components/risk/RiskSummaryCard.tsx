import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, ApiError, isNotFoundError } from '../../services/api';
import { AlertTriangle, BarChart3 } from 'lucide-react';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

interface RiskSummaryCardProps {
  caseId: string;
}

export const RiskSummaryCard: React.FC<RiskSummaryCardProps> = ({ caseId }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['risk-summary', caseId],
    queryFn: () => api.getCaseRiskSummary(caseId),
    enabled: !!caseId,
  });

  if (isLoading) {
    return (
      <div className="p-4 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] flex items-center gap-3 text-xs text-[var(--color-on-surface-variant)] font-medium">
        <div className="w-4 h-4 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        <span>Loading case risk summary...</span>
      </div>
    );
  }

  if (isNotFoundError(error)) {
    return (
      <div className="p-4 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
          <BarChart3 className="w-4 h-4 text-[var(--color-on-surface-variant)]" />
          <span>Case Risk Summary</span>
        </div>
        <p className="text-xs text-[var(--color-on-surface-variant)] leading-relaxed font-medium">
          No risk summary yet — run a trace or request a risk calculation.
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 bg-red-950/20 rounded-xl border border-red-900/50 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-[var(--color-error)] shrink-0" />
        <span className="text-[11px] font-bold text-red-400 uppercase tracking-wider">
          {error instanceof ApiError ? error.code || 'RISK_SUMMARY_FAILED' : 'RISK_SUMMARY_FAILED'}
        </span>
      </div>
    );
  }

  const distribution = Object.entries(data.risk_distribution || {});
  const maxCount = Math.max(1, ...distribution.map(([, count]) => count));

  return (
    <div className="p-4 bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)] space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-[var(--color-primary)]" />
          <span className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
            Case Risk Summary
          </span>
        </div>
        <ProvenanceBadge variant="derived" />
      </div>

      <div className="grid grid-cols-2 gap-3 text-center">
        <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
          <div className="text-xl font-bold text-[var(--color-on-surface)]">{data.wallet_count}</div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-on-surface-variant)] mt-1">Wallets scored</div>
        </div>
        <div className="p-3 bg-[var(--color-surface-dim)] rounded-lg border border-[var(--color-outline)]">
          <div className="text-xl font-bold text-[var(--color-tertiary)]">
            {data.average_score != null ? Math.round(data.average_score) : '—'}
          </div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-on-surface-variant)] mt-1">Average score</div>
        </div>
      </div>

      <div className="space-y-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-on-surface-variant)]">
          Risk Distribution
        </span>
        {distribution.length === 0 ? (
          <p className="text-xs font-medium text-[var(--color-on-surface-variant)]">No scored wallets in this trace yet.</p>
        ) : (
          <ul className="space-y-2.5">
            {distribution.map(([category, count]) => (
              <li key={category} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-[var(--color-on-surface-variant)] uppercase tracking-wider">{category}</span>
                  <span className="text-[var(--color-on-surface)]">{count}</span>
                </div>
                <div className="h-1.5 bg-[var(--color-surface-dim)] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      category.toLowerCase().includes('critical') ||
                      category.toLowerCase().includes('high')
                        ? 'bg-red-500'
                        : category.toLowerCase().includes('medium') ||
                            category.toLowerCase().includes('moderate')
                          ? 'bg-amber-500'
                          : 'bg-green-500'
                    }`}
                    style={{ width: `${(count / maxCount) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {data.highest_risk_wallet && (
        <div className="pt-3 border-t border-[var(--color-outline)] flex items-center justify-between gap-2 text-xs font-semibold">
          <span className="text-[var(--color-on-surface-variant)] uppercase tracking-wider">Highest risk wallet</span>
          <span className="text-red-400 break-all text-right text-[11px] font-bold">
            {data.highest_risk_wallet.slice(0, 10)}…{' '}
            {data.highest_risk_score != null ? `(${data.highest_risk_score})` : ''}
          </span>
        </div>
      )}
    </div>
  );
};
