import React, { useMemo, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
  ReactFlowProvider,
  useReactFlow,
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
import { ProvenanceBadge } from '../common/ProvenanceBadge';
import { RefreshCw, Layers, ZoomIn, ZoomOut, Maximize2, Play } from 'lucide-react';

interface FundFlowCanvasProps {
  trace: TraceResponse | null;
  isLoading?: boolean;
  onExecuteTrace?: () => void;
}

const nodeTypes = {
  addressNode: AddressNode,
};

const edgeTypes = {
  transferEdge: TransferEdge,
};

const CanvasControls: React.FC<{
  nodes: Node[];
  onRelayout: () => void;
  nodeCount: number;
  edgeCount: number;
  maxHop: number;
  isDemo?: boolean;
}> = ({ nodes, onRelayout, nodeCount, edgeCount, maxHop, isDemo }) => {
  const { zoomIn, zoomOut, fitView, setCenter, getZoom, setViewport } = useReactFlow();

  const handleFitOrFocus = useCallback(() => {
    const seedNode = nodes.find((n) => (n.data as any)?.hop === 0) || nodes[0];
    const currentZoom = getZoom();

    // If currently at overview scale (<= 0.70) or already fitted, focus on the primary seed target wallet
    if (currentZoom <= 0.70 && seedNode) {
      setCenter(seedNode.position.x + 120, seedNode.position.y + 68, {
        zoom: 0.95,
        duration: 450,
      });
    } else {
      // Otherwise smoothly fit the entire graph into the viewport
      fitView({
        padding: 0.22,
        duration: 450,
        minZoom: 0.35,
        maxZoom: 1.1,
      });
    }
  }, [nodes, getZoom, setCenter, fitView]);

  return (
    <>
      <Controls
        showInteractive={false}
        showFitView={false}
        className="!border-[var(--color-outline)]"
      >
        <button
          type="button"
          onClick={handleFitOrFocus}
          className="react-flow__controls-button react-flow__controls-fitview cursor-pointer"
          title="Fit Graph to Screen / Focus Seed Target (Toggle)"
          aria-label="fit view"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 30">
            <path d="M3.692 4.63c0-.53.4-.938.939-.938h5.215V0H4.708C2.13 0 0 2.054 0 4.63v5.216h3.692V4.631zM27.354 0h-5.2v3.692h5.17c.53 0 .984.4.984.939v5.215H32V4.631A4.624 4.624 0 0027.354 0zm.954 24.83c0 .532-.4.94-.939.94h-5.215v3.768h5.215c2.577 0 4.631-2.13 4.631-4.707v-5.139h-3.692v5.139zm-23.677.94c-.531 0-.939-.4-.939-.94v-5.138H0v5.139c0 2.577 2.13 4.707 4.708 4.707h5.138V25.77H4.631z" />
          </svg>
        </button>
      </Controls>

      <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5 bg-[var(--color-surface-container)] p-1.5 rounded-xl border border-[var(--color-outline)] shadow-lg font-[JetBrains_Mono] text-xs font-bold text-[var(--color-on-surface-variant)]">
        <button
          type="button"
          onClick={onRelayout}
          title="Recalculate Hierarchical DAG Layout"
          className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer border border-transparent hover:border-[var(--color-outline)]"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <div className="h-4 w-px bg-[var(--color-outline)]" />
        <button
          type="button"
          onClick={() => zoomIn({ duration: 250 })}
          title="Zoom In (+)"
          className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer border border-transparent hover:border-[var(--color-outline)]"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => zoomOut({ duration: 250 })}
          title="Zoom Out (-)"
          className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer border border-transparent hover:border-[var(--color-outline)]"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={handleFitOrFocus}
          title="Fit Graph / Focus Seed Target (Toggle)"
          className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer border border-transparent hover:border-[var(--color-outline)]"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => {
            const seedNode = nodes.find((n) => (n.data as any)?.hop === 0) || nodes[0];
            if (seedNode) {
              setCenter(seedNode.position.x + 120, seedNode.position.y + 68, { zoom: 1.0, duration: 250 });
            } else {
              setViewport({ x: 80, y: 80, zoom: 1.0 }, { duration: 250 });
            }
          }}
          title="Reset Zoom (1:1 Focus on Target)"
          className="px-2 py-1 rounded-lg text-[10px] text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)] transition-colors cursor-pointer border border-transparent hover:border-[var(--color-outline)]"
        >
          1:1
        </button>
        <div className="h-4 w-px bg-[var(--color-outline)]" />
        <span className="px-2 text-[10px]">
          <strong className="text-[var(--color-on-surface)]">{nodeCount}</strong> NODES |{' '}
          <strong className="text-[var(--color-on-surface)]">{edgeCount}</strong> TRANSFERS |{' '}
          MAX HOP <strong className="text-[var(--color-on-surface)]">{maxHop}</strong>
        </span>
        <div className="h-4 w-px bg-[var(--color-outline)]" />
        <ProvenanceBadge variant={isDemo ? 'demo' : 'live'} size="sm" />
      </div>
    </>
  );
};

export const FundFlowCanvas: React.FC<FundFlowCanvasProps> = ({
  trace,
  isLoading,
  onExecuteTrace,
}) => {
  const { selectNode, selectEdge, currentCase } = useInvestigationStore();

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
        blockchain: trace.blockchain,
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
        color: 'var(--color-primary)',
      },
      animated: true,
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
      <div className="w-full h-full flex flex-col items-center justify-center bg-transparent text-[var(--color-on-surface-variant)]">
        <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider font-[JetBrains_Mono]">
          Executing Bounded Multi-Hop BFS Trace...
        </p>
        <p className="text-[11px] text-[var(--color-on-surface-variant)] mt-0.5 font-medium font-[JetBrains_Mono]">
          Traversing on-chain transfers & reconstructing fund movement graph
        </p>
      </div>
    );
  }

  if (!trace?.graph || trace.graph.nodes.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-transparent text-[var(--color-on-surface-variant)] p-8 border border-dashed border-[var(--color-outline)] rounded-2xl m-4 font-[Inter]">
        <Layers className="w-10 h-10 text-[var(--color-on-surface-variant)] mb-2" />
        <h3 className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wide">
          NO ACTIVE GRAPH TRACE LOADED
        </h3>
        <p className="text-[11px] text-[var(--color-on-surface-variant)] text-center max-w-sm mt-1 mb-4">
          Execute a multi-hop trace on this wallet to construct and inspect the forensic fund flow graph.
        </p>
        {onExecuteTrace && (
          <button
            type="button"
            onClick={onExecuteTrace}
            className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] hover:brightness-110 text-[var(--color-on-primary)] rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>EXECUTE INITIAL TRACE</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="w-full h-full relative bg-transparent">
      <ReactFlowProvider>
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
          fitViewOptions={{ padding: 0.18, includeHiddenNodes: false }}
          minZoom={0.2}
          maxZoom={3.0}
          className="bg-transparent"
        >
          <Background
            color="var(--color-outline-variant)"
            gap={24}
            size={1}
            variant={BackgroundVariant.Dots}
          />
          <MiniMap
            nodeColor={(n) => {
              if (n.data?.hop === 0) return 'var(--color-error)';
              if (n.data?.hop === 1) return 'var(--color-tertiary)';
              if (n.data?.hop === 2) return 'var(--color-secondary)';
              return 'var(--color-primary)';
            }}
            className="!bg-[var(--color-surface-container-low)] !border-[var(--color-outline)]"
            maskColor="var(--color-surface-dim)"
          />
          <CanvasControls
            nodes={nodes}
            onRelayout={handleRelayout}
            nodeCount={trace.graph.node_count}
            edgeCount={trace.graph.edge_count}
            maxHop={trace.graph.max_hop_depth}
            isDemo={Boolean(currentCase?.demo_data)}
          />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
};
