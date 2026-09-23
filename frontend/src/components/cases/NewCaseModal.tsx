import React, { useState } from 'react';
import { X, ShieldAlert, AlertCircle, ArrowRight } from 'lucide-react';
import type { BlockchainType, CaseCreatePayload, FraudType } from '../../types';

interface NewCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: CaseCreatePayload) => Promise<void>;
}

export const NewCaseModal: React.FC<NewCaseModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState<CaseCreatePayload>({
    title: '',
    reported_wallet_address: '',
    reported_transaction_hash: '',
    blockchain: 'ethereum',
    fraud_type: 'investment_scam',
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
        reported_amount: formData.reported_amount ? Number(formData.reported_amount) : null,
        reported_transaction_hash: formData.reported_transaction_hash?.trim() || null,
        investigator_notes: formData.investigator_notes?.trim() || null,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create case');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-xs">
      <div className="bg-[#121620] border border-[#1F2637] rounded-lg max-w-xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-[#1F2637] flex items-center justify-between bg-[#0D1017]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded bg-blue-900/40 border border-blue-700/50 text-blue-400">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-100 uppercase tracking-wide">
                Initialize New Investigation
              </h2>
              <p className="text-xs text-slate-400">
                Register case docket and seed address for multi-hop graph tracing
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 bg-red-950/60 border border-red-800 rounded flex items-center gap-2 text-xs text-red-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Case Title / Incident Identifier <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g., Op Apollo: Victim Deposit Drain 0x93F"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-sans"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Reported Seed Wallet Address <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="0x..."
              value={formData.reported_wallet_address}
              onChange={(e) => setFormData({ ...formData, reported_wallet_address: e.target.value })}
              className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Initial Deposit Tx Hash (Optional)
            </label>
            <input
              type="text"
              placeholder="0x..."
              value={formData.reported_transaction_hash || ''}
              onChange={(e) => setFormData({ ...formData, reported_transaction_hash: e.target.value })}
              className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Blockchain
              </label>
              <select
                value={formData.blockchain}
                onChange={(e) => setFormData({ ...formData, blockchain: e.target.value as BlockchainType })}
                className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-blue-500 font-mono cursor-pointer"
              >
                <option value="ethereum">Ethereum (Mainnet)</option>
                <option value="tron">Tron (TRC-20)</option>
                <option value="bitcoin">Bitcoin (BTC)</option>
                <option value="solana">Solana (SPL)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Fraud Typology
              </label>
              <select
                value={formData.fraud_type}
                onChange={(e) => setFormData({ ...formData, fraud_type: e.target.value as FraudType })}
                className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-blue-500 cursor-pointer"
              >
                <option value="investment_scam">Investment Scam</option>
                <option value="phishing">Phishing / Drainer</option>
                <option value="ransomware">Ransomware</option>
                <option value="task_based_fraud">Task-Based Fraud</option>
                <option value="sextortion">Sextortion</option>
                <option value="darknet">Darknet Market</option>
                <option value="other">Other Incident</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Reported Amount
              </label>
              <input
                type="number"
                step="any"
                placeholder="0.00"
                value={formData.reported_amount ?? ''}
                onChange={(e) => setFormData({ ...formData, reported_amount: e.target.value })}
                className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Asset Symbol
              </label>
              <input
                type="text"
                placeholder="ETH, USDT, USDC"
                value={formData.reported_asset || ''}
                onChange={(e) => setFormData({ ...formData, reported_asset: e.target.value.toUpperCase() })}
                className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Preliminary Investigator Notes
            </label>
            <textarea
              rows={3}
              placeholder="Provide case narrative or referral background..."
              value={formData.investigator_notes || ''}
              onChange={(e) => setFormData({ ...formData, investigator_notes: e.target.value })}
              className="w-full bg-[#090B10] border border-[#1F2637] rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="pt-3 border-t border-[#1F2637] flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <span>Registering Case...</span>
              ) : (
                <>
                  <span>Create Investigation Docket</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
