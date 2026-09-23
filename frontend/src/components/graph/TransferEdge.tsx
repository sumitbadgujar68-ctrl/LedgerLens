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

export const TransferEdge: React.FC<EdgeProps<TransferEdgeData>> = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const amount = data?.amount !== undefined ? Number(data.amount).toLocaleString(undefined, { maximumFractionDigits: 4 }) : '—';
  const asset = data?.asset || 'ETH';

  return (
    <>
      <path
        id={id}
        className={`react-flow__edge-path transition-all stroke-2 ${
          selected ? 'stroke-blue-400 stroke-[3px]' : 'stroke-slate-600 hover:stroke-slate-400'
        }`}
        d={edgePath}
        markerEnd="url(#arrow)"
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className={`px-2 py-0.5 rounded border text-[10px] font-mono shadow-md cursor-pointer transition-all ${
            selected
              ? 'bg-blue-950 text-blue-200 border-blue-400 font-bold scale-105'
              : 'bg-[#0D1017] text-slate-300 border-[#1F2637] hover:border-slate-500'
          }`}
        >
          <span className="text-emerald-400 font-bold">{amount}</span> {asset}
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

TransferEdge.displayName = 'TransferEdge';
