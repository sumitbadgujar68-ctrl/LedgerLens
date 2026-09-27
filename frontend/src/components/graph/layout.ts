import dagre from 'dagre';
import type { Node, Edge } from 'reactflow';

export const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction = 'LR'
) => {
  if (!nodes || nodes.length === 0) {
    return { nodes: [], edges };
  }

  // Check if nodes have hop metadata
  const hasHops = nodes.some((n) => typeof (n.data as any)?.hop === 'number');

  if (hasHops) {
    const nodeWidth = 240;
    const nodeHeight = 135;
    const colGap = 70;
    const rowGap = 35;
    const hopGap = 110;

    // Group nodes by hop
    const hopMap = new Map<number, Node[]>();
    nodes.forEach((node) => {
      const hop = Number((node.data as any)?.hop ?? 0);
      if (!hopMap.has(hop)) {
        hopMap.set(hop, []);
      }
      hopMap.get(hop)!.push(node);
    });

    const sortedHops = Array.from(hopMap.keys()).sort((a, b) => a - b);

    // Calculate layout structure for each hop
    const hopConfigs = sortedHops.map((hop) => {
      const hopNodes = hopMap.get(hop)!;
      const count = hopNodes.length;

      // Determine max rows per column for this hop to maintain balanced aspect ratio
      let maxRows = 4;
      if (count <= 3) maxRows = count;
      else if (count <= 8) maxRows = 4;
      else if (count <= 16) maxRows = 4;
      else maxRows = 5;

      const numCols = Math.ceil(count / maxRows);
      const actualRows = Math.min(count, maxRows);
      const totalHopHeight = actualRows * (nodeHeight + rowGap) - rowGap;
      const totalHopWidth = numCols * (nodeWidth + colGap) - colGap;

      return {
        hop,
        nodes: hopNodes,
        maxRows,
        numCols,
        actualRows,
        totalHopHeight,
        totalHopWidth,
      };
    });

    // Find the maximum height across all hops to vertically center each hop
    const maxGraphHeight = Math.max(
      ...hopConfigs.map((c) => c.totalHopHeight),
      nodeHeight
    );

    let currentX = 60;
    const layoutedNodes: Node[] = [];

    hopConfigs.forEach((config) => {
      const startY = (maxGraphHeight - config.totalHopHeight) / 2 + 50;

      config.nodes.forEach((node, idx) => {
        const colIdx = Math.floor(idx / config.maxRows);
        const rowIdx = idx % config.maxRows;

        const x = currentX + colIdx * (nodeWidth + colGap);
        const y = startY + rowIdx * (nodeHeight + rowGap);

        layoutedNodes.push({
          ...node,
          position: { x, y },
        });
      });

      currentX += config.totalHopWidth + hopGap;
    });

    return { nodes: layoutedNodes, edges };
  }

  // Fallback to Dagre if no hop metadata is present
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 260;
  const nodeHeight = 140;

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 80,
    ranksep: 140,
    marginx: 60,
    marginy: 50,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};