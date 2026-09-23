import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { HopBadge, AddressDisplay } from '../common/Badge';
import { Wallet } from 'lucide-react';

export interface AddressNodeData {
  id: string;
  label?: string;
  hop: number;
  type: string;
  metadata?: {
    balance?: string | number;
    transaction_count?: number;
    tags?: string[];
    [key: string]: unknown;
  };
  isSelected?: boolean;
}

export const AddressNode: React.FC<NodeProps<AddressNodeData>> = memo(({ data, selected }) => {
  const hop = data.hop ?? 0;
  const address = data.id || '';
  const isSeed = hop === 0;

  const hopBorderColor: Record<number, string> = {
    0: 'border-red-500/80 shadow-[0_0_12px_rgba(239,68,68,0.25)]',
    1: 'border-amber-500/80 shadow-[0_0_10px_rgba(245,158,11,0.2)]',
    2: 'border-blue-500/80 shadow-[0_0_10px_rgba(59,130,246,0.2)]',
  };
  const borderStyle = hopBorderColor[hop] || 'border-emerald-500/80 shadow-[0_0_10px_rgba(16,185,129,0.2)]';

  return (
    <div
      className={`min-w-[220px] max-w-[260px] bg-[#121620] rounded-md border text-slate-200 transition-all ${
        selected ? 'ring-2 ring-blue-400 border-blue-400' : borderStyle
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="w-2.5 h-2.5 bg-blue-500 border border-slate-900"
      />

      <div className="p-2.5 bg-[#0D1017]/90 border-b border-[#1F2637] flex items-center justify-between">
        <HopBadge hop={hop} />
        {isSeed && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
            SEED TARGET
          </span>
        )}
      </div>

      <div className="p-3 space-y-2">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-slate-800 text-slate-400">
            <Wallet className="w-3.5 h-3.5" />
          </div>
          <AddressDisplay address={address} className="text-xs" />
        </div>

        <div className="grid grid-cols-2 gap-1.5 pt-1.5 border-t border-[#1F2637] text-[11px] text-slate-400 font-mono">
          <div>
            <span className="text-slate-400 text-[10px] block">TYPE</span>
            <span className="text-slate-200">{data.type || 'EOA'}</span>
          </div>
          {data.metadata?.transaction_count !== undefined && (
            <div>
              <span className="text-slate-400 text-[10px] block">TXS</span>
              <span className="text-slate-200">{data.metadata.transaction_count}</span>
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-2.5 h-2.5 bg-emerald-500 border border-slate-900"
      />
    </div>
  );
});

AddressNode.displayName = 'AddressNode';
