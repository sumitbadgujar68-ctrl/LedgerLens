import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { HopBadge, AddressDisplay } from '../common/Badge';
import { Wallet, ShieldAlert, Building2, Shuffle } from 'lucide-react';

export interface AddressNodeData {
  id: string;
  label?: string;
  hop: number;
  type: string;
  blockchain?: string;
  metadata?: {
    balance?: string | number;
    transaction_count?: number;
    tags?: string[];
    [key: string]: unknown;
  };
  isSelected?: boolean;
}

export const AddressNode: React.FC<NodeProps<AddressNodeData>> = memo(
  ({ data, selected }) => {
    const hop = data.hop ?? 0;
    const address = data.id || '';
    const isSeed = hop === 0;

    // Detect node nature for icon & tag
    const isMixer =
      data.label?.toLowerCase().includes('tornado') ||
      data.type?.toLowerCase().includes('mixer') ||
      data.metadata?.tags?.some((t) => t.toLowerCase().includes('mixer'));
    const isCex =
      data.label?.toLowerCase().includes('binance') ||
      data.label?.toLowerCase().includes('exchange') ||
      data.type?.toLowerCase().includes('cex') ||
      data.metadata?.tags?.some((t) => t.toLowerCase().includes('exchange'));
    const isContract =
      data.type?.toLowerCase().includes('contract') ||
      data.label?.toLowerCase().includes('contract') ||
      data.label?.toLowerCase().includes('disperser');

    const borderStyle = isSeed
      ? 'border-[var(--color-error)] shadow-[0_0_14px_rgba(248,81,73,0.18)]'
      : isMixer
      ? 'border-[var(--color-error)] bg-[var(--color-surface-container)]'
      : isCex
      ? 'border-[var(--color-secondary-fixed)] bg-[var(--color-surface-container)]'
      : hop === 1
      ? 'border-[var(--color-tertiary)]/50'
      : 'border-[var(--color-outline)]';

    return (
      <div
        className={`w-[200px] bg-[var(--color-surface-container-low)] rounded-lg border text-[var(--color-on-surface)] transition-all font-[Inter] select-none ${
          selected
            ? 'ring-2 ring-[#00F0FF] border-[#00F0FF] shadow-[0_0_16px_rgba(0,240,255,0.2)]'
            : borderStyle
        }`}
      >
        <Handle
          type="target"
          position={Position.Left}
          className="w-2 h-2 !bg-[var(--color-secondary-fixed)] !border !border-[var(--color-surface-container-low)]"
        />

        {/* ── Header ── */}
        <div className="px-2.5 py-1.5 bg-[var(--color-surface-container)] border-b border-[var(--color-outline)] flex items-center justify-between rounded-t-lg">
          <HopBadge hop={hop} />
          {isSeed ? (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-[var(--color-error)]/10 text-[var(--color-error)] border border-[var(--color-error)]/30 font-bold tracking-wider font-[JetBrains_Mono]">
              TARGET
            </span>
          ) : isMixer ? (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-[var(--color-error)]/10 text-[var(--color-error)] border border-[var(--color-error)]/40 font-bold tracking-wider font-[JetBrains_Mono]">
              MIXER
            </span>
          ) : isCex ? (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-[var(--color-secondary)]/10 text-[var(--color-secondary-fixed)] border border-[var(--color-secondary)]/30 font-bold tracking-wider font-[JetBrains_Mono]">
              CEX
            </span>
          ) : data.label ? (
            <span className="text-[9px] font-bold text-[var(--color-on-surface-variant)] truncate max-w-[90px] font-[Inter]">
              {data.label}
            </span>
          ) : null}
        </div>

        {/* ── Body ── */}
        <div className="px-2.5 py-2 flex items-center gap-2">
          <div className="p-1 rounded-md bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)] flex-shrink-0">
            {isMixer ? (
              <ShieldAlert className="w-3 h-3 text-[var(--color-error)]" />
            ) : isCex ? (
              <Building2 className="w-3 h-3 text-[var(--color-secondary-fixed)]" />
            ) : isContract ? (
              <Shuffle className="w-3 h-3 text-[var(--color-tertiary)]" />
            ) : (
              <Wallet className="w-3 h-3 text-[var(--color-on-surface-variant)]" />
            )}
          </div>
          <AddressDisplay address={address} className="text-[11px] font-[JetBrains_Mono]" blockchain={data.blockchain as string | undefined} />
        </div>

        {/* ── Footer: type + tx count ── */}
        <div className="px-2.5 pb-2 flex items-center justify-between text-[9px] text-[var(--color-on-surface-variant)] font-[JetBrains_Mono] border-t border-[var(--color-outline)] pt-1.5">
          <span className="uppercase tracking-wide">
            {isMixer
              ? 'Mixer Pool'
              : isCex
              ? 'CEX Wallet'
              : isContract
              ? 'Contract'
              : data.type || 'EOA'}
          </span>
          {data.metadata?.transaction_count !== undefined && (
            <span className="font-bold text-[var(--color-on-surface)]">
              {data.metadata.transaction_count} txs
            </span>
          )}
        </div>

        <Handle
          type="source"
          position={Position.Right}
          className="w-2 h-2 !bg-[#00F0FF] !border-2 !border-[var(--color-surface-container-low)]"
        />
      </div>
    );
  }
);

AddressNode.displayName = 'AddressNode';
