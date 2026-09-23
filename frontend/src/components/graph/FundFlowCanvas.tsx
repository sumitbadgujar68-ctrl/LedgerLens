import React, { useMemo, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
} from 'reactflow';
import type {
  Node,
  Edge,
  NodeMouseHandler,
  EdgeMouseHandler,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { AddressNode } from './AddressNode';
import { TransferEdge } from './TransferEdge';
import { getLayoutedElements } from './layout';
import type { TraceResponse } from '../../types';
import { useInvestigationStore } from '../../store/investigationStore';
import { RefreshCw, Layers } from 'lucide-react';

interface FundFlowCanvasProps {
  trace: TraceResponse | null;
  isLoading?: boolean;
}

const nodeTypes = {
  addressNode: AddressNode,
};

const edgeTypes = {
  transferEdge: TransferEdge,
};

export const FundFlowCanvas: React.FC<FundFlowCanvasProps> = ({ trace, isLoading }) => {
  const { selectNode, selectEdge } = useInvestigationStore();

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!trace?.graph?.nodes || trace.graph.nodes.length === 0) {
      return { nodes: [] as Node[], edges: [] as Edge[] };
    }

    const rawNodes: Node[] = trace.graph.nodes.map((n) => ({
      id: n.id,
      type: 'addressNode',
      position: { x: 0, y: 0 },
      data: {
        id: n.id,
        label: n.label,
        hop: n.hop,
        type: n.type,
        metadata: n.metadata,
      },
    }));

    const rawEdges: Edge[] = trace.graph.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'transferEdge',
      data: {
        transaction_hash: e.transaction_hash,
        amount: e.amount,
        asset: e.asset,
        hop: e.hop,
        timestamp: e.timestamp,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#64748B',
      },
    }));

    return getLayoutedElements(rawNodes, rawEdges);
  }, [trace]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      const graphNode = trace?.graph?.nodes.find((n) => n.id === node.id) || {
        id: node.id,
        type: node.data.type || 'wallet',
        hop: node.data.hop || 0,
        metadata: node.data.metadata || {},
      };
      selectNode(graphNode);
    },
    [trace, selectNode]
  );

  const onEdgeClick: EdgeMouseHandler = useCallback(
    (_, edge) => {
      const graphEdge = trace?.graph?.edges.find((e) => e.id === edge.id) || {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'transfer',
        transaction_hash: edge.data?.transaction_hash || '',
        amount: edge.data?.amount || 0,
        asset: edge.data?.asset || 'ETH',
        hop: edge.data?.hop || 0,
      };
      selectEdge(graphEdge);
    },
    [trace, selectEdge]
  );

  const handleRelayout = () => {
    const layouted = getLayoutedElements(nodes, edges);
    setNodes([...layouted.nodes]);
    setEdges([...layouted.edges]);
  };

  if (isLoading) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#090B10] text-slate-400">
        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
          Executing Bounded Multi-Hop BFS Trace...
        </p>
        <p className="text-xs text-slate-400 mt-1 font-mono">
          Fetching transfers from Alchemy provider & expanding graph
        </p>
      </div>
    );
  }

  if (!trace?.graph || trace.graph.nodes.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#090B10] text-slate-400 p-8 border border-dashed border-[#1F2637] rounded-lg m-4">
        <Layers className="w-12 h-12 text-slate-600 mb-3" />
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
          No Fund-Flow Graph Data
        </h3>
        <p className="text-xs text-slate-400 text-center max-w-md mt-1 mb-4">
          Launch a bounded trace from the parameter toolbar above to query on-chain transfers and reconstruct the multi-hop movement of funds.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative bg-[#090B10]">
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-[#121620]/90 p-1.5 rounded border border-[#1F2637] shadow-lg backdrop-blur-xs">
        <button
          onClick={handleRelayout}
          title="Recalculate Hierarchical DAG Layout"
          className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <div className="h-4 w-px bg-[#1F2637]" />
        <span className="text-[11px] font-mono text-slate-400 px-1">
          {trace.graph.node_count} WALLETS | {trace.graph.edge_count} TRANSFERS | MAX HOP {trace.graph.max_hop_depth}
        </span>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.2}
        maxZoom={2.5}
        className="bg-[#090B10]"
      >
        <Background
          color="#1F2637"
          gap={20}
          size={1}
          variant={BackgroundVariant.Dots}
        />
        <Controls className="!bg-[#121620] !border-[#1F2637] !fill-slate-300" />
        <MiniMap
          nodeColor={(n) => {
            if (n.data?.hop === 0) return '#EF4444';
            if (n.data?.hop === 1) return '#F59E0B';
            if (n.data?.hop === 2) return '#3B82F6';
            return '#10B981';
          }}
          className="!bg-[#0D1017] !border-[#1F2637]"
          maskColor="rgba(9, 11, 16, 0.7)"
        />
      </ReactFlow>
    </div>
  );
};
