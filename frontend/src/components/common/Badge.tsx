import React, { useState } from 'react';
import { Copy, Check, ExternalLink } from 'lucide-react';

interface CopyButtonProps {
  value: string;
  className?: string;
  iconOnly?: boolean;
}

export const CopyButton: React.FC<CopyButtonProps> = ({
  value,
  className = '',
  iconOnly = false,
}) => {
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
      type="button"
      title="Copy to clipboard"
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-semibold text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors border border-transparent hover:border-[var(--color-outline)] cursor-pointer ${className}`}
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-[var(--color-secondary)]" />
      ) : (
        <Copy className="w-3.5 h-3.5" />
      )}
      {!iconOnly && <span>{copied ? 'Copied' : 'Copy'}</span>}
    </button>
  );
};

export const getExplorerUrl = (blockchain: string | undefined, type: 'address' | 'tx', value: string) => {
  const chain = (blockchain || 'ethereum').toLowerCase();
  switch (chain) {
    case 'bitcoin':
      return type === 'address' ? `https://blockstream.info/address/${value}` : `https://blockstream.info/tx/${value}`;
    case 'tron':
      return type === 'address' ? `https://tronscan.org/#/address/${value}` : `https://tronscan.org/#/transaction/${value}`;
    case 'ethereum':
    default:
      return type === 'address' ? `https://etherscan.io/address/${value}` : `https://etherscan.io/tx/${value}`;
  }
};

export const AddressDisplay: React.FC<{
  address: string;
  copyable?: boolean;
  truncate?: boolean;
  className?: string;
  showExplorer?: boolean;
  blockchain?: string;
}> = ({
  address,
  copyable = true,
  truncate = true,
  className = '',
  showExplorer = false,
  blockchain,
}) => {
  const displayAddress =
    truncate && address.length > 14
      ? `${address.substring(0, 8)}...${address.substring(address.length - 6)}`
      : address;

  return (
    <span
      className={`inline-flex items-center gap-2 font-bold text-sm text-[var(--color-on-surface)] ${className}`}
    >
      <span
        title={address}
        className="hover:text-[var(--color-primary)] hover:underline cursor-pointer select-all font-semibold"
      >
        {displayAddress}
      </span>
      {copyable && <CopyButton value={address} iconOnly />}
      {showExplorer && (
        <a
          href={getExplorerUrl(blockchain, 'address', address)}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-blue-400 hover:text-blue-300 transition-colors p-1 rounded hover:bg-[var(--color-surface-container-high)]"
          title={`Open in ${blockchain || 'ethereum'} explorer`}
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      )}
    </span>
  );
};

export const TxHashDisplay: React.FC<{
  hash: string;
  copyable?: boolean;
  truncate?: boolean;
  className?: string;
  showExplorer?: boolean;
  blockchain?: string;
}> = ({
  hash,
  copyable = true,
  truncate = true,
  className = '',
  showExplorer = true,
  blockchain,
}) => {
  const displayHash =
    truncate && hash.length > 16
      ? `${hash.substring(0, 10)}...${hash.substring(hash.length - 8)}`
      : hash;

  return (
    <span
      className={`inline-flex items-center gap-2 font-bold text-sm text-[var(--color-on-surface)] ${className}`}
    >
      <span
        title={hash}
        className="hover:text-[var(--color-primary)] hover:underline cursor-pointer select-all font-semibold"
      >
        {displayHash}
      </span>
      {copyable && <CopyButton value={hash} iconOnly />}
      {showExplorer && (
        <a
          href={getExplorerUrl(blockchain, 'tx', hash)}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-blue-400 hover:text-blue-300 transition-colors p-1 rounded hover:bg-[var(--color-surface-container-high)]"
          title={`Open transaction on ${blockchain || 'ethereum'} explorer`}
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      )}
    </span>
  );
};

export const StatusBadge: React.FC<{
  status?: string;
  blockchain?: string;
  className?: string;
}> = ({
  status = 'unknown',
  blockchain = 'ethereum',
  className = '',
}) => {
  const chain = (blockchain || 'ethereum').toLowerCase();
  const raw = (status || '').toLowerCase().trim();
  const clean = raw.replace(/_/g, ' ');

  let label = clean.toUpperCase();
  let colorStyle = 'bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border-[var(--color-outline)]';

  if (clean === 'success' || clean === 'confirmed') {
    label = chain === 'bitcoin' || chain === 'tron' ? 'CONFIRMED' : 'SUCCESS';
    colorStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (clean === 'failed') {
    label = 'FAILED';
    colorStyle = 'bg-red-500/10 text-red-400 border-red-500/30';
  } else if (clean === 'pending' || clean === 'unconfirmed') {
    label = chain === 'bitcoin' ? 'UNCONFIRMED' : 'PENDING';
    colorStyle = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (clean === 'unavailable') {
    label = 'UNAVAILABLE';
    colorStyle = 'bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border-[var(--color-outline)]';
  } else if (
    clean.includes('active') ||
    clean.includes('under investigation') ||
    clean.includes('in review')
  ) {
    label = clean.toUpperCase();
    colorStyle = 'bg-blue-500/10 text-blue-400 border-blue-500/30';
  } else if (clean.includes('closed') || clean.includes('completed') || clean.includes('sealed')) {
    label = clean.toUpperCase();
    colorStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else {
    label = 'UNKNOWN';
    colorStyle = 'bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border-[var(--color-outline)]';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded-lg border uppercase tracking-wider ${colorStyle} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current" />
      {label}
    </span>
  );
};

export const RiskBadge: React.FC<{
  score?: number;
  level?: string;
  className?: string;
}> = ({ score, level, className = '' }) => {
  const numScore = score ?? 0;
  const isCritical = numScore >= 90 || level?.toLowerCase() === 'critical';
  const isHigh =
    (numScore >= 70 && numScore < 90) ||
    level?.toLowerCase() === 'high' ||
    level?.toLowerCase() === 'high risk';
  const isMed =
    (numScore >= 40 && numScore < 70) || level?.toLowerCase() === 'medium';

  let colorStyle = 'bg-[var(--color-secondary)]/10 text-green-400 border-green-500/30';
  let labelText = `LOW ${numScore > 0 ? `· ${numScore}` : ''}`;

  if (isCritical) {
    colorStyle = 'bg-red-500/15 text-[var(--color-error)] border-red-500/40';
    labelText = `CRITICAL ${numScore > 0 ? `· ${numScore}` : ''}`;
  } else if (isHigh) {
    colorStyle = 'bg-[var(--color-error)]/10 text-red-400 border-red-500/30';
    labelText = `HIGH ${numScore > 0 ? `· ${numScore}` : ''}`;
  } else if (isMed) {
    colorStyle = 'bg-[var(--color-tertiary)]/10 text-[var(--color-tertiary)] border-amber-500/30';
    labelText = `MEDIUM ${numScore > 0 ? `· ${numScore}` : ''}`;
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 text-[10px] font-bold rounded-lg border uppercase tracking-wider ${colorStyle} ${className}`}
    >
      {labelText}
    </span>
  );
};

export const HopBadge: React.FC<{ hop: number }> = ({ hop }) => {
  const hopColors: Record<number, string> = {
    0: 'bg-[var(--color-error)]/10 text-[var(--color-error)] border-red-500/30',
    1: 'bg-[var(--color-tertiary)]/10 text-[var(--color-tertiary)] border-amber-500/30',
    2: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    3: 'bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border-green-500/30',
  };
  const color =
    hopColors[hop] || 'bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border-[var(--color-outline)]';

  return (
    <span
      className={`inline-flex items-center px-2 py-1 text-[10px] font-bold rounded-lg border tracking-wider uppercase ${color}`}
    >
      {hop === 0 ? 'SEED (HOP 0)' : `HOP ${hop}`}
    </span>
  );
};

export const NetworkChip: React.FC<{ network: string; className?: string }> = ({
  network,
  className = '',
}) => {
  const upper = network.toUpperCase();
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-lg border bg-[var(--color-surface-container-low)] text-[var(--color-on-surface-variant)] border-[var(--color-outline)] ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)]" />
      {upper === 'ETHEREUM' ? 'ETH MAINNET' : upper}
    </span>
  );
};
