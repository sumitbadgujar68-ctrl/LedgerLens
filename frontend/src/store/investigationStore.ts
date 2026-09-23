import { create } from 'zustand';
import type { Case, CanonicalTransaction, GraphEdge, GraphNode, TraceResponse } from '../types';

export interface EvidenceNote {
  id: string;
  caseId: string;
  timestamp: string;
  author: string;
  content: string;
  tag?: 'lead' | 'custody' | 'subpoena' | 'general';
}

interface InvestigationState {
  currentCase: Case | null;
  currentTrace: TraceResponse | null;
  
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  selectedTransaction: CanonicalTransaction | null;
  
  isInspectorOpen: boolean;
  inspectorMode: 'node' | 'edge' | 'transaction' | null;
  
  activeBottomTab: 'ledger' | 'evidence' | 'timeline' | 'errors';
  
  evidenceNotes: EvidenceNote[];
  
  setCurrentCase: (c: Case | null) => void;
  setCurrentTrace: (t: TraceResponse | null) => void;
  selectNode: (node: GraphNode | null) => void;
  selectEdge: (edge: GraphEdge | null) => void;
  selectTransaction: (tx: CanonicalTransaction | null) => void;
  setInspectorOpen: (open: boolean) => void;
  setActiveBottomTab: (tab: 'ledger' | 'evidence' | 'timeline' | 'errors') => void;
  addEvidenceNote: (note: Omit<EvidenceNote, 'id' | 'timestamp'>) => void;
  closeInspector: () => void;
}

export const useInvestigationStore = create<InvestigationState>((set) => ({
  currentCase: null,
  currentTrace: null,
  
  selectedNode: null,
  selectedEdge: null,
  selectedTransaction: null,
  
  isInspectorOpen: false,
  inspectorMode: null,
  
  activeBottomTab: 'ledger',
  
  evidenceNotes: [
    {
      id: 'note-1',
      caseId: 'demo',
      timestamp: new Date().toISOString(),
      author: 'Investigator #402',
      content: 'Initial seed address identified from victim scam report. Primary outflow observed at Hop 1.',
      tag: 'lead',
    },
  ],
  
  setCurrentCase: (currentCase) => set({ currentCase }),
  setCurrentTrace: (currentTrace) => set({ currentTrace }),
  
  selectNode: (node) => set({
    selectedNode: node,
    selectedEdge: null,
    selectedTransaction: null,
    isInspectorOpen: !!node,
    inspectorMode: node ? 'node' : null,
  }),
  
  selectEdge: (edge) => set({
    selectedEdge: edge,
    selectedNode: null,
    selectedTransaction: null,
    isInspectorOpen: !!edge,
    inspectorMode: edge ? 'edge' : null,
  }),
  
  selectTransaction: (tx) => set({
    selectedTransaction: tx,
    selectedNode: null,
    selectedEdge: null,
    isInspectorOpen: !!tx,
    inspectorMode: tx ? 'transaction' : null,
  }),
  
  setInspectorOpen: (isInspectorOpen) => set({ isInspectorOpen }),
  
  setActiveBottomTab: (activeBottomTab) => set({ activeBottomTab }),
  
  addEvidenceNote: (note) => set((state) => ({
    evidenceNotes: [
      {
        ...note,
        id: `note-${Date.now()}`,
        timestamp: new Date().toISOString(),
      },
      ...state.evidenceNotes,
    ],
  })),
  
  closeInspector: () => set({
    isInspectorOpen: false,
    selectedNode: null,
    selectedEdge: null,
    selectedTransaction: null,
    inspectorMode: null,
  }),
}));
