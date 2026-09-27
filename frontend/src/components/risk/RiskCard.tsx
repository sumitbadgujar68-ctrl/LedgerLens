import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, ApiError, isNotFoundError } from '../../services/api';
import { AlertTriangle, ChevronDown, ChevronUp, Gauge, ShieldAlert } from 'lucide-react';
import { ProvenanceBadge } from '../common/ProvenanceBadge';

interface RiskCardProps {
  caseId: string;
  walletAddress: string;
}

function evidenceCounts(evidence: {
  transaction_hashes: string[];
  pattern_ids: string[];
  attribution_ids: string[];
  entity_ids: string[];
  wallet_addresses: string[];
}): Array<{ label: string; count: number }> {
  return [
    { label: 'tx hashes', count: evidence.transaction_hashes?.length ?? 0 },
    { label: 'patterns', count: evidence.pattern_ids?.length ?? 0 },
    { label: 'attributions', count: evidence.attribution_ids?.length ?? 0 },
    { label: 'entities', count: evidence.entity_ids?.length ?? 0 },
    { label: 'wallets', count: evidence.wallet_addresses?.length ?? 0 },
  ].filter((item) => item.count > 0);
}

function categoryColor(category: string): string {
  const normalized = (category || '').toLowerCase();
  if (normalized.includes('critical') || normalized.includes('severe')) return 'text-red-400';
  if (normalized.includes('high')) return 'text-orange-400';
  if (normalized.includes('medium') || normalized.includes('moderate')) return 'text-amber-400';
  if (normalized.includes('low')) return 'text-emerald-400';
  return 'text-slate-200';
}

export const RiskCard: React.FC<RiskCardProps> = ({ caseId, walletAddress }) => {
  const [showExplanation, setShowExplanation] = useState(false);

  const {
    data: risk,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['risk', caseId, walletAddress.toLowerCase()],
    queryFn: () => api.getWalletRisk(caseId, walletAddress),
    enabled: !!caseId && !!walletAddress,
  });

  const {
    data: explanation,
    isLoading: explanationLoading,
    error: explanationError,
  } = useQuery({
    queryKey: ['risk-explanation', risk?.risk_score_id],
    queryFn: () => api.getRiskExplanation(risk!.risk_score_id),
    enabled: showExplanation && !!risk?.risk_score_id,
  });

  if (!caseId || !walletAddress) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] flex items-center gap-3 text-xs text-[var(--color-on-surface-variant)] font-medium">
        <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        <span>Calculating risk score...</span>
      </div>
    );
  }

  if (isNotFoundError(error)) {
    return (
      <div className="p-4 bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
          <Gauge className="w-4 h-4 text-[var(--color-on-surface-variant)]" />
          <span>Risk Score</span>
        </div>
        <p className="text-xs text-[var(--color-on-surface-variant)] leading-relaxed font-medium">
          No risk score yet — run a trace or request a risk calculation.
        </p>
      </div>
    );
  }

  if (error || !risk) {
    const code = error instanceof ApiError ? error.code : undefined;
    return (
      <div className="p-4 bg-red-950/20 rounded-2xl border border-red-900/50 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[var(--color-error)] uppercase tracking-wider">
          <AlertTriangle className="w-4 h-4" />
          <span>{code || 'RISK_LOOKUP_FAILED'}</span>
        </div>
        <p className="text-xs text-red-400 font-medium">
          Unable to load the risk score for this wallet.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[var(--color-surface-container-low)] rounded-2xl border border-[var(--color-outline)] p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-[var(--color-primary)]" />
            <span className="text-xs font-bold text-[var(--color-on-surface-variant)] uppercase tracking-wider">Risk Score</span>
          </div>
          <ProvenanceBadge variant="derived" />
        </div>
        <span className="text-[11px] font-bold text-[var(--color-on-surface-variant)]">{risk.scoring_version}</span>
      </div>

      <div className="flex items-end justify-between gap-3">
        <div className="text-4xl font-bold text-[var(--color-on-surface)] leading-none">
          {risk.score}
          <span className="text-base text-[var(--color-on-surface-variant)] font-semibold font-[Inter]">/100</span>
        </div>
        <span
          className={`text-xs font-bold uppercase tracking-widest px-2 py-1 rounded-md bg-[var(--color-surface-dim)] border border-[var(--color-outline)] ${categoryColor(risk.risk_category)}`}
        >
          {risk.risk_category}
        </span>
      </div>

      <div className="h-2 bg-[var(--color-surface-dim)] rounded-full overflow-hidden border border-[var(--color-outline)]">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            risk.score >= 70 ? 'bg-red-500' : risk.score >= 40 ? 'bg-amber-500' : 'bg-green-500'
          }`}
          style={{ width: `${Math.max(0, Math.min(100, risk.score))}%` }}
        />
      </div>

      <div className="space-y-3 pt-3 border-t border-[var(--color-outline)]">
        <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-on-surface-variant)]">
          Contributing Factors ({risk.factors.length})
        </span>
        {risk.factors.length === 0 ? (
          <p className="text-xs text-[var(--color-on-surface-variant)] font-medium">No risk factors recorded for this score.</p>
        ) : (
          <ul className="space-y-3">
            {risk.factors.map((factor, index) => {
              const counts = evidenceCounts(factor.evidence);
              return (
                <li
                  key={`${factor.factor_type}-${index}`}
                  className="p-3 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)] space-y-2"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
                      {factor.factor_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[11px] font-bold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded-md">
                      w={factor.weight} · conf {Math.round(Number(factor.confidence) * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-[var(--color-on-surface-variant)] leading-relaxed font-medium">{factor.description}</p>
                  {counts.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {counts.map((c) => (
                        <span
                          key={c.label}
                          className="text-[10px] font-bold px-2 py-1 rounded-md bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] text-[var(--color-on-surface-variant)] uppercase tracking-wider"
                        >
                          {c.count} {c.label}
                        </span>
                      ))}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="pt-3 border-t border-[var(--color-outline)] space-y-3">
        <button
          onClick={() => setShowExplanation((v) => !v)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-[var(--color-surface-dim)] hover:bg-[var(--color-surface-container-high)] border border-[var(--color-outline)] rounded-xl text-xs font-bold text-[var(--color-on-surface)] transition-colors cursor-pointer"
        >
          <ShieldAlert className="w-4 h-4 text-[var(--color-tertiary)]" />
          <span>{showExplanation ? 'Hide Explanation' : 'Explain Risk Profile'}</span>
          {showExplanation ? <ChevronUp className="w-4 h-4 text-[var(--color-on-surface-variant)]" /> : <ChevronDown className="w-4 h-4 text-[var(--color-on-surface-variant)]" />}
        </button>

        {showExplanation && (
          <div data-testid="risk-explanation" className="space-y-3 p-4 bg-[var(--color-surface-dim)] rounded-xl border border-[var(--color-outline)]">
            {explanationLoading && (
              <div className="flex items-center gap-3 text-xs text-[var(--color-on-surface-variant)] font-medium">
                <div className="w-4 h-4 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
                <span>Generating explanation via Copilot AI...</span>
              </div>
            )}

            {explanationError && (
              <p className="text-xs font-bold text-[var(--color-error)]">
                {explanationError instanceof ApiError
                  ? explanationError.code || 'EXPLANATION_FAILED'
                  : 'EXPLANATION_FAILED'}
              </p>
            )}

            {explanation && (
              <>
                <p className="text-xs text-[var(--color-on-surface)] leading-relaxed font-medium">{explanation.summary}</p>
                <ul className="space-y-2">
                  {explanation.factor_explanations.map((line, index) => (
                    <li
                      key={index}
                      className="text-xs text-[var(--color-on-surface-variant)] leading-relaxed flex gap-2 font-medium"
                    >
                      <span className="text-[var(--color-primary)] font-bold">›</span>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
                <div className="text-[11px] font-bold text-[var(--color-on-surface-variant)] pt-3 border-t border-[var(--color-outline)] uppercase tracking-wider">
                  Total Score: {explanation.total_score}/100 · {explanation.risk_category} ·{' '}
                  {explanation.scoring_version}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div className="text-[11px] font-semibold text-[var(--color-on-surface-variant)]">
        Calculated {new Date(risk.calculated_at).toLocaleString()}
      </div>
    </div>
  );
};
