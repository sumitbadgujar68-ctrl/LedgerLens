import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CopyButtonProps {
  value: string;
  className?: string;
  iconOnly?: boolean;
}

export const CopyButton: React.FC<CopyButtonProps> = ({ value, className = '', iconOnly = false }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      title="Copy to clipboard"
      className={`inline-flex items-center gap-1.5 px-1.5 py-0.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors ${className}`}
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      {!iconOnly && <span>{copied ? 'Copied' : 'Copy'}</span>}
    </button>
  );
};

export const AddressDisplay: React.FC<{ address: string; copyable?: boolean; truncate?: boolean; className?: string }> = ({
  address,
  copyable = true,
  truncate = true,
  className = '',
}) => {
  const displayAddress = truncate && address.length > 14
    ? `${address.substring(0, 8)}...${address.substring(address.length - 6)}`
    : address;

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono text-sm ${className}`}>
      <span title={address} className="text-slate-300 hover:text-white cursor-pointer select-all">
        {displayAddress}
      </span>
      {copyable && <CopyButton value={address} iconOnly />}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const normalized = status.toLowerCase().replace('_', ' ');
  let colorStyle = 'bg-blue-950/60 text-blue-400 border-blue-800/60';

  if (normalized.includes('active') || normalized.includes('under investigation')) {
    colorStyle = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
  } else if (normalized.includes('closed') || normalized.includes('completed')) {
    colorStyle = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
  } else if (normalized.includes('archived')) {
    colorStyle = 'bg-slate-900 text-slate-400 border-slate-700';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded border uppercase tracking-wider ${colorStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current animate-pulse" />
      {normalized}
    </span>
  );
};

export const HopBadge: React.FC<{ hop: number }> = ({ hop }) => {
  const hopColors: Record<number, string> = {
    0: 'bg-red-950/80 text-red-400 border-red-700/80',
    1: 'bg-amber-950/80 text-amber-400 border-amber-700/80',
    2: 'bg-blue-950/80 text-blue-400 border-blue-700/80',
  };
  const color = hopColors[hop] || 'bg-emerald-950/80 text-emerald-400 border-emerald-700/80';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[11px] font-mono font-bold rounded border ${color}`}>
      {hop === 0 ? 'SEED (HOP 0)' : `HOP ${hop}`}
    </span>
  );
};
