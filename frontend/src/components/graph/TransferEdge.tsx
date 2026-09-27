import React, { memo } from 'react';
import { getBezierPath, EdgeLabelRenderer } from 'reactflow';
import type { EdgeProps } from 'reactflow';

export interface TransferEdgeData {
  transaction_hash: string;
  amount: string | number;
  asset?: string | null;
  hop: number;
  timestamp?: string | null;
}

export const TransferEdge: React.FC<EdgeProps<TransferEdgeData>> = memo(
  ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    selected,
    animated,
  }) => {
    const [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    });

    const amount =
      data?.amount !== undefined
        ? Number(data.amount).toLocaleString(undefined, {
            maximumFractionDigits: 4,
          })
        : '—';
    const asset = data?.asset || 'ETH';

    const strokeColor = selected ? 'var(--color-primary)' : 'var(--color-primary)';
    const strokeWidth = selected ? 3 : 2;
    const filter = selected
      ? 'drop-shadow(0 0 4px rgba(255,159,67,0.7))'
      : 'drop-shadow(0 0 2px rgba(255,159,67,0.25))';

    return (
      <>
        {/* Animated dashes to show flow direction */}
        <path
          id={`${id}-bg`}
          d={edgePath}
          stroke="rgba(255,159,67,0.12)"
          strokeWidth={strokeWidth + 4}
          fill="none"
          strokeLinecap="round"
        />
        <path
          id={id}
          className={animated ? 'react-flow__edge-path animated' : 'react-flow__edge-path'}
          d={edgePath}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={selected ? '0' : '6 4'}
          style={{
            filter,
            transition: 'stroke 0.2s, stroke-width 0.2s',
          }}
        />
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className={`px-2 py-0.5 rounded border text-[10px] font-[JetBrains_Mono] shadow-sm cursor-pointer transition-all ${
              selected
                ? 'bg-[var(--color-surface-container)] text-[#00F0FF] border-[#00F0FF]/60 font-bold ring-1 ring-[#00F0FF]/40'
                : 'bg-[var(--color-surface-container-low)] text-[var(--color-on-surface-variant)] border-[var(--color-outline)] hover:border-[#00F0FF]/50 hover:text-[var(--color-on-surface)] font-semibold'
            }`}
          >
            <span className="font-bold" style={{ color: selected ? '#00F0FF' : 'var(--color-tertiary)' }}>{amount}</span>{' '}{asset}
          </div>
        </EdgeLabelRenderer>
      </>
    );
  }
);

TransferEdge.displayName = 'TransferEdge';
