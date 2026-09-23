import { describe, it, expect, beforeEach } from 'vitest';
import { useInvestigationStore } from '../store/investigationStore';
import type { GraphNode, CanonicalTransaction } from '../types';

describe('useInvestigationStore', () => {
  beforeEach(() => {
    useInvestigationStore.setState({
      currentCase: null,
      currentTrace: null,
      selectedNode: null,
      selectedEdge: null,
      selectedTransaction: null,
      isInspectorOpen: false,
      inspectorMode: null,
      activeBottomTab: 'ledger',
    });
  });

  it('selects a graph node and opens the inspector in node mode', () => {
    const node: GraphNode = {
      id: '0x1234567890abcdef1234567890abcdef12345678',
      type: 'wallet',
      hop: 1,
      metadata: { transaction_count: 5 },
    };

    useInvestigationStore.getState().selectNode(node);

    const state = useInvestigationStore.getState();
    expect(state.selectedNode).toEqual(node);
    expect(state.isInspectorOpen).toBe(true);
    expect(state.inspectorMode).toBe('node');
  });

  it('selects a transaction and opens the inspector in transaction mode', () => {
    const tx: CanonicalTransaction = {
      chain: 'ethereum',
      transaction_hash: '0xabc123',
      from_address: '0xfrom',
      to_address: '0xto',
      amount: '1.5',
      decimals: 18,
      asset_type: 'native',
      transfer_category: 'external',
      transaction_type: 'transfer',
      status: 'CONFIRMED',
      provider: 'AlchemyProvider',
      provider_reference: 'ref',
    };

    useInvestigationStore.getState().selectTransaction(tx);

    const state = useInvestigationStore.getState();
    expect(state.selectedTransaction).toEqual(tx);
    expect(state.isInspectorOpen).toBe(true);
    expect(state.inspectorMode).toBe('transaction');
  });

  it('adds an evidence note properly', () => {
    useInvestigationStore.getState().addEvidenceNote({
      caseId: 'case-123',
      author: 'Investigator #402',
      content: 'Critical outflow discovered.',
      tag: 'lead',
    });

    const state = useInvestigationStore.getState();
    expect(state.evidenceNotes.length).toBeGreaterThan(0);
    expect(state.evidenceNotes[0].content).toBe('Critical outflow discovered.');
  });
});
