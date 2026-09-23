import React, { useState } from 'react';
import { useInvestigationStore } from '../../store/investigationStore';
import { 
  X, 
  ExternalLink, 
  FileText, 
  ShieldCheck, 
  Hash, 
  Wallet, 
  ArrowRight, 
  Lock,
  Plus
} from 'lucide-react';
import { AddressDisplay, CopyButton, HopBadge, StatusBadge } from '../common/Badge';

export const InspectorDrawer: React.FC = () => {
  const {
    isInspectorOpen,
    inspectorMode,
    selectedNode,
    selectedEdge,
    selectedTransaction,
    closeInspector,
    addEvidenceNote,
    currentCase,
  } = useInvestigationStore();

  const [noteContent, setNoteContent] = useState('');
  const [noteTag, setNoteTag] = useState<'lead' | 'custody' | 'subpoena' | 'general'>('lead');
  const [showNoteForm, setShowNoteForm] = useState(false);

  if (!isInspectorOpen || !inspectorMode) {
    return null;
  }

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteContent.trim()) return;

    addEvidenceNote({
      caseId: currentCase?.case_id || 'unassigned',
      author: 'Investigator #402',
      content: noteContent,
      tag: noteTag,
    });
    setNoteContent('');
    setShowNoteForm(false);
  };

  return (
    <div className="w-96 bg-[#161B26] border-l border-[#1F2637] flex flex-col h-full overflow-hidden shadow-2xl shrink-0 z-20">
      <div className="p-4 bg-[#0D1017] border-b border-[#1F2637] flex items-center justify-between">
        <div className="flex items-center gap-2">
          {inspectorMode === 'node' && <Wallet className="w-4 h-4 text-blue-400" />}
          {inspectorMode === 'edge' && <ArrowRight className="w-4 h-4 text-emerald-400" />}
          {inspectorMode === 'transaction' && <Hash className="w-4 h-4 text-amber-400" />}
          <h2 className="text-xs font-semibold text-slate-100 uppercase tracking-wider">
            {inspectorMode === 'node' && 'Wallet Address Dossier'}
            {inspectorMode === 'edge' && 'Transfer Provenance'}
            {inspectorMode === 'transaction' && 'Cryptographic Tx Inspector'}
          </h2>
        </div>
        <button
          onClick={closeInspector}
          className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {inspectorMode === 'node' && selectedNode && (
          <>
            <div className="p-3 bg-[#121620] rounded border border-[#1F2637] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">TARGET IDENTIFIER</span>
                <HopBadge hop={selectedNode.hop} />
              </div>
              <div className="font-mono text-xs text-slate-200 break-all select-all">
                {selectedNode.id}
              </div>
              <div className="pt-2 border-t border-[#1F2637] flex items-center justify-between">
                <CopyButton value={selectedNode.id} />
                <a
                  href={`https://etherscan.io/address/${selectedNode.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <span>Etherscan</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Verifiable On-Chain Attributes</span>
              </h3>
              <div className="bg-[#121620] rounded border border-[#1F2637] p-3 text-xs space-y-2 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Entity Classification:</span>
                  <span className="text-slate-200">{selectedNode.type || 'EOA (External Owned)'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Hop Distance from Seed:</span>
                  <span className="text-slate-200">{selectedNode.hop}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Graph Outflow Count:</span>
                  <span className="text-slate-200">
                    {selectedNode.metadata?.transaction_count ?? 'Derived via BFS'}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-slate-400" />
                  <span>VASP & Risk Attribution</span>
                </h3>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  PHASE 4
                </span>
              </div>
              <div className="bg-[#121620]/60 rounded border border-[#1F2637] p-3 text-xs space-y-2 text-slate-400">
                <div className="flex justify-between">
                  <span>VASP Identification:</span>
                  <span className="font-mono italic">Awaiting Phase 4 Activation</span>
                </div>
                <div className="flex justify-between">
                  <span>Risk Typology Score:</span>
                  <span className="font-mono italic">Not Calculated (MVP)</span>
                </div>
              </div>
            </div>
          </>
        )}

        {inspectorMode === 'edge' && selectedEdge && (
          <>
            <div className="p-3 bg-[#121620] rounded border border-[#1F2637] space-y-2">
              <span className="text-[11px] font-mono text-slate-400 block">VALUE TRANSFERRED</span>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {Number(selectedEdge.amount).toLocaleString(undefined, { maximumFractionDigits: 6 })} {selectedEdge.asset || 'ETH'}
              </div>
              <div className="text-xs text-slate-400 font-mono">
                Hop Depth: {selectedEdge.hop}
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Transfer Flow
              </h3>
              <div className="bg-[#121620] rounded border border-[#1F2637] p-3 space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 text-[10px] font-mono block">FROM (ORIGIN)</span>
                  <AddressDisplay address={selectedEdge.source} />
                </div>
                <div className="flex justify-center text-slate-400">
                  <ArrowRight className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] font-mono block">TO (DESTINATION)</span>
                  <AddressDisplay address={selectedEdge.target} />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Transaction Hash
              </h3>
              <div className="bg-[#121620] rounded border border-[#1F2637] p-3 text-xs space-y-2">
                <div className="font-mono text-slate-200 break-all select-all text-[11px]">
                  {selectedEdge.transaction_hash}
                </div>
                <div className="pt-2 border-t border-[#1F2637] flex items-center justify-between">
                  <CopyButton value={selectedEdge.transaction_hash} />
                  <a
                    href={`https://etherscan.io/tx/${selectedEdge.transaction_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    <span>Etherscan</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          </>
        )}

        {inspectorMode === 'transaction' && selectedTransaction && (
          <>
            <div className="p-3 bg-[#121620] rounded border border-[#1F2637] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">TRANSACTION HASH</span>
                <StatusBadge status={selectedTransaction.status || 'CONFIRMED'} />
              </div>
              <div className="font-mono text-xs text-slate-200 break-all select-all">
                {selectedTransaction.transaction_hash}
              </div>
              <div className="pt-2 border-t border-[#1F2637] flex items-center justify-between">
                <CopyButton value={selectedTransaction.transaction_hash} />
                <a
                  href={`https://etherscan.io/tx/${selectedTransaction.transaction_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <span>Etherscan</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>On-Chain Execution Data</span>
              </h3>
              <div className="bg-[#121620] rounded border border-[#1F2637] p-3 text-xs space-y-2 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Block Number:</span>
                  <span className="text-slate-200">{selectedTransaction.block_number ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Timestamp:</span>
                  <span className="text-slate-200">
                    {selectedTransaction.block_timestamp
                      ? new Date(selectedTransaction.block_timestamp).toLocaleString()
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Transfer Category:</span>
                  <span className="text-slate-200 uppercase">{selectedTransaction.transfer_category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Gas Used:</span>
                  <span className="text-slate-200">{selectedTransaction.gas_used?.toLocaleString() ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Gas Fee:</span>
                  <span className="text-slate-200">{selectedTransaction.total_fee ? `${selectedTransaction.total_fee} ETH` : '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Provider:</span>
                  <span className="text-emerald-400">{selectedTransaction.provider}</span>
                </div>
              </div>
            </div>
          </>
        )}

        <div className="pt-2 border-t border-[#1F2637] space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              <span>Investigator Case Notes</span>
            </h3>
            {!showNoteForm && (
              <button
                onClick={() => setShowNoteForm(true)}
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Note</span>
              </button>
            )}
          </div>

          {showNoteForm && (
            <form onSubmit={handleAddNote} className="space-y-2 bg-[#121620] p-3 rounded border border-[#1F2637]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300">Tag:</span>
                <select
                  value={noteTag}
                  onChange={(e) => setNoteTag(e.target.value as any)}
                  className="bg-[#090B10] border border-[#1F2637] rounded px-2 py-1 text-xs text-slate-200"
                >
                  <option value="lead">Investigative Lead</option>
                  <option value="custody">Chain of Custody</option>
                  <option value="subpoena">Subpoena Target</option>
                  <option value="general">General Note</option>
                </select>
              </div>
              <textarea
                rows={3}
                required
                placeholder="Record observation regarding this artifact..."
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                className="w-full bg-[#090B10] border border-[#1F2637] rounded p-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNoteForm(false)}
                  className="px-2.5 py-1 bg-slate-800 text-slate-400 rounded text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1 bg-blue-600 text-white rounded text-xs font-semibold cursor-pointer"
                >
                  Save Note
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
