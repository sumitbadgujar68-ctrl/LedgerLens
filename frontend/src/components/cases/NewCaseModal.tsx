import React, { useState } from 'react';
import { X, ShieldAlert, AlertCircle, Plus } from 'lucide-react';
import type { BlockchainType, CaseCreatePayload, FraudType } from '../../types';

interface NewCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: CaseCreatePayload) => Promise<void>;
}

export const NewCaseModal: React.FC<NewCaseModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [formData, setFormData] = useState<CaseCreatePayload>({
    title: '',
    reported_wallet_address: '',
    reported_transaction_hash: '',
    blockchain: 'ethereum',
    fraud_type: 'phishing',
    reported_amount: '',
    reported_asset: 'ETH',
    investigator_notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.reported_wallet_address.trim()) {
      setError('Case title and target wallet address are required.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await onSubmit({
        ...formData,
        reported_amount: formData.reported_amount
          ? Number(formData.reported_amount)
          : null,
        reported_transaction_hash:
          formData.reported_transaction_hash?.trim() || null,
        investigator_notes: formData.investigator_notes?.trim() || null,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create case docket');
    } finally {
      setLoading(false);
    }
  };

  const handleAddressChange = (addr: string) => {
    const trimmed = addr.trim();
    let detected: BlockchainType = formData.blockchain;
    if (/^0x[a-fA-F0-9]{40}$/.test(trimmed)) detected = 'ethereum';
    else if (/^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$/.test(trimmed)) detected = 'bitcoin';
    else if (/^T[a-zA-Z0-9]{25,35}$/.test(trimmed)) detected = 'tron';
    setFormData({ ...formData, reported_wallet_address: addr, blockchain: detected });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--color-outline)] flex items-center justify-between bg-[var(--color-surface-dim)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-[var(--color-primary)]">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--color-on-surface)] tracking-wide">
                Initialize New Investigation Docket
              </h2>
              <p className="text-xs text-[var(--color-on-surface-variant)] mt-0.5">
                Register seed wallet identifier for multi-hop graph expansion &amp; evidence custody
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] p-2 rounded-xl hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 bg-red-950/20 border border-red-900/50 rounded-xl flex items-center gap-2 text-xs text-red-400 font-medium">
              <AlertCircle className="w-4 h-4 shrink-0 text-[var(--color-error)]" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5">
              Case Title / Typology Reference <span className="text-[var(--color-error)]">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g., Op Apollo: Victim Deposit Drain 0x93F"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-on-surface)] placeholder-slate-600 focus:outline-none focus:border-[var(--color-primary)] transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5 flex items-center justify-between">
              <span>Reported Seed Wallet Address <span className="text-[var(--color-error)]">*</span></span>
              {formData.reported_wallet_address && (
                <span className="text-[10px] font-mono text-[var(--color-primary)] uppercase">
                  DETECTED: {formData.blockchain}
                </span>
              )}
            </label>
            <input
              type="text"
              required
              placeholder="0x... / bc1... / T..."
              value={formData.reported_wallet_address}
              onChange={(e) => handleAddressChange(e.target.value)}
              className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-on-surface)] placeholder-slate-600 focus:outline-none focus:border-[var(--color-primary)] transition-colors font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5">
                Blockchain Network
              </label>
              <select
                value={formData.blockchain}
                onChange={(e) =>
                  setFormData({ ...formData, blockchain: e.target.value as BlockchainType })
                }
                className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
              >
                <option value="ethereum">Ethereum Mainnet</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5">
                Fraud Typology
              </label>
              <select
                value={formData.fraud_type}
                onChange={(e) =>
                  setFormData({ ...formData, fraud_type: e.target.value as FraudType })
                }
                className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
              >
                <option value="phishing">Phishing Drainer</option>
                <option value="investment_scam">High-Yield Investment Scam</option>
                <option value="ransomware">Ransomware Extortion</option>
                <option value="darknet">Darknet Marketplace</option>
                <option value="task_based_fraud">Task-Based Fraud</option>
                <option value="other">Other Incident</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5">
                Reported Loss Volume
              </label>
              <input
                type="number"
                step="any"
                placeholder="Amount (optional)"
                value={formData.reported_amount ?? ''}
                onChange={(e) =>
                  setFormData({ ...formData, reported_amount: e.target.value })
                }
                className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-on-surface)] placeholder-slate-600 focus:outline-none focus:border-[var(--color-primary)] transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5">
                Asset Symbol
              </label>
              <input
                type="text"
                placeholder="Asset symbol (optional)"
                value={formData.reported_asset ?? ''}
                onChange={(e) =>
                  setFormData({ ...formData, reported_asset: e.target.value })
                }
                className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-on-surface)] placeholder-slate-600 focus:outline-none focus:border-[var(--color-primary)] transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--color-on-surface-variant)] mb-1.5">
              Sworn Investigator Notes / Case Log
            </label>
            <textarea
              rows={3}
              placeholder="Initial intelligence context, victim reporting narrative, or external referral notes..."
              value={formData.investigator_notes || ''}
              onChange={(e) =>
                setFormData({ ...formData, investigator_notes: e.target.value })
              }
              className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-xl px-4 py-3 text-sm text-[var(--color-on-surface)] placeholder-slate-600 focus:outline-none focus:border-[var(--color-primary)] transition-colors resize-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-5 mt-2 border-t border-[var(--color-outline)] flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-[var(--color-surface-dim)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] border border-[var(--color-outline)] transition-colors cursor-pointer font-medium text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-[var(--color-primary)] hover:bg-[#e06810] text-[var(--color-on-surface)] font-bold flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50 text-sm shadow-[0_0_15px_rgba(249,115,22,0.3)] hover:shadow-[0_0_20px_rgba(249,115,22,0.5)]"
            >
              <Plus className="w-4 h-4" />
              <span>{loading ? 'Initializing Docket...' : 'CREATE & INVESTIGATE'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

