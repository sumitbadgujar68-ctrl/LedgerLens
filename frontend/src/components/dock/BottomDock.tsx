import React from 'react';
import { useInvestigationStore } from '../../store/investigationStore';
import { 
  Table, 
  FileText, 
  Terminal, 
  ChevronUp, 
  ChevronDown,
} from 'lucide-react';
import { AddressDisplay, StatusBadge } from '../common/Badge';

export const BottomDock: React.FC = () => {
  const {
    currentTrace,
    activeBottomTab,
    setActiveBottomTab,
    selectTransaction,
    evidenceNotes,
  } = useInvestigationStore();

  const [isCollapsed, setIsCollapsed] = React.useState(false);

  const transactions = currentTrace?.transactions || [];

  return (
    <div className={`bg-[#0E1119] border-t border-[#1F2637] transition-all duration-200 flex flex-col z-10 ${
      isCollapsed ? 'h-10' : 'h-64'
    }`}>
      {/* Dock Tab Bar */}
      <div className="h-10 bg-[#0D1017] px-4 flex items-center justify-between border-b border-[#1F2637] shrink-0 select-none">
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setActiveBottomTab('ledger');
              setIsCollapsed(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold font-mono transition-colors cursor-pointer ${
              activeBottomTab === 'ledger' && !isCollapsed
                ? 'bg-[#161B26] text-blue-400 border border-blue-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            <span>TRANSACTIONS ({transactions.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveBottomTab('evidence');
              setIsCollapsed(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold font-mono transition-colors cursor-pointer ${
              activeBottomTab === 'evidence' && !isCollapsed
                ? 'bg-[#161B26] text-blue-400 border border-blue-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>EVIDENCE NOTES ({evidenceNotes.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveBottomTab('timeline');
              setIsCollapsed(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold font-mono transition-colors cursor-pointer ${
              activeBottomTab === 'timeline' && !isCollapsed
                ? 'bg-[#161B26] text-blue-400 border border-blue-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>TELEMETRY & LOGS</span>
          </button>
        </div>

        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 text-slate-400 hover:text-slate-200 rounded hover:bg-slate-800 transition-colors cursor-pointer"
        >
          {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Dock Content Body */}
      {!isCollapsed && (
        <div className="flex-1 overflow-auto bg-[#090B10]">
          {activeBottomTab === 'ledger' && (
            <div className="w-full">
              {transactions.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400 font-mono">
                  No canonical transactions loaded for this trace.
                </div>
              ) : (
                <table className="w-full text-left text-xs font-mono border-collapse">
                  <thead className="bg-[#121620] sticky top-0 text-[11px] text-slate-400 border-b border-[#1F2637]">
                    <tr>
                      <th className="p-2.5">TX HASH</th>
                      <th className="p-2.5">FROM</th>
                      <th className="p-2.5">TO</th>
                      <th className="p-2.5 text-right">AMOUNT</th>
                      <th className="p-2.5">ASSET</th>
                      <th className="p-2.5">CATEGORY</th>
                      <th className="p-2.5">BLOCK / TIME</th>
                      <th className="p-2.5">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1F2637]/50 text-slate-300">
                    {transactions.map((tx) => (
                      <tr
                        key={tx.transaction_hash}
                        onClick={() => selectTransaction(tx)}
                        className="hover:bg-[#161B26] cursor-pointer transition-colors"
                      >
                        <td className="p-2.5 text-blue-400 font-mono">
                          <AddressDisplay address={tx.transaction_hash} />
                        </td>
                        <td className="p-2.5">
                          <AddressDisplay address={tx.from_address} />
                        </td>
                        <td className="p-2.5">
                          {tx.to_address ? <AddressDisplay address={tx.to_address} /> : '—'}
                        </td>
                        <td className="p-2.5 text-right font-bold text-emerald-400">
                          {Number(tx.amount).toLocaleString(undefined, { maximumFractionDigits: 6 })}
                        </td>
                        <td className="p-2.5 text-slate-300">{tx.asset || 'ETH'}</td>
                        <td className="p-2.5 text-slate-400 uppercase text-[10px]">
                          {tx.transfer_category}
                        </td>
                        <td className="p-2.5 text-slate-400 text-[11px]">
                          {tx.block_number ? `#${tx.block_number}` : '—'}
                        </td>
                        <td className="p-2.5">
                          <StatusBadge status={tx.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {activeBottomTab === 'evidence' && (
            <div className="p-4 space-y-3 max-w-4xl">
              {evidenceNotes.length === 0 ? (
                <div className="text-xs text-slate-400 font-mono">
                  No evidence notes recorded. Add notes via the Inspector Drawer.
                </div>
              ) : (
                evidenceNotes.map((note) => (
                  <div key={note.id} className="p-3 bg-[#121620] rounded border border-[#1F2637] space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">{note.author}</span>
                        {note.tag && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-950 text-blue-400 border border-blue-800 uppercase">
                            {note.tag}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {new Date(note.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-sans">{note.content}</p>
                  </div>
                ))
              )}
            </div>
          )}

          {activeBottomTab === 'timeline' && (
            <div className="p-4 font-mono text-xs text-slate-400 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400">
                <Terminal className="w-4 h-4" />
                <span>TRACE EXECUTION AUDIT LOG</span>
              </div>
              <div className="p-3 bg-[#121620] rounded border border-[#1F2637] space-y-1 text-[11px] leading-relaxed">
                <div>[SYSTEM] Trace ID: {currentTrace?.trace_id || 'UNEXECUTED'}</div>
                <div>[SYSTEM] Blockchain: {currentTrace?.blockchain || 'ethereum'}</div>
                <div>[SYSTEM] Provider Reference: {currentTrace?.provider || 'AlchemyProvider (alchemy_network=eth-mainnet)'}</div>
                <div>[SYSTEM] Result Status: {currentTrace?.result_status || 'READY'}</div>
                <div>[SYSTEM] Wallets Discovered: {currentTrace?.summary?.wallet_count ?? 0}</div>
                <div>[SYSTEM] Transfers Traced: {currentTrace?.summary?.transaction_count ?? 0}</div>
                <div>[SYSTEM] Max Depth: {currentTrace?.summary?.max_hop_depth ?? 0} hops</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
