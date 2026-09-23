import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { CaseCreatePayload } from '../../types';
import { TopBar } from '../layout/TopBar';
import { NewCaseModal } from '../cases/NewCaseModal';
import { AddressDisplay, StatusBadge } from '../common/Badge';
import { 
  FolderSearch, 
  Layers, 
  DollarSign, 
  Activity, 
  ArrowUpRight, 
  Search,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [chainFilter, setChainFilter] = useState('all');

  const { data: cases = [], isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.getCases(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: CaseCreatePayload) => api.createCase(payload),
    onSuccess: (newCase) => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
      navigate(`/cases/${newCase.case_id}`);
    },
  });

  const totalCases = cases.length;
  const activeCases = cases.filter((c) => c.status === 'active' || c.status === 'under_investigation').length;
  const totalTrackedAmount = cases.reduce((sum, c) => sum + (Number(c.reported_amount) || 0), 0);

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.case_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.reported_wallet_address.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchesChain = chainFilter === 'all' || c.blockchain === chainFilter;

    return matchesSearch && matchesStatus && matchesChain;
  });

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#090B10]">
      <TopBar onNewCase={() => setIsModalOpen(true)} />

      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#121620] border border-[#1F2637] rounded p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>ACTIVE INVESTIGATIONS</span>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-100">
              {activeCases} <span className="text-xs font-normal text-slate-400">/ {totalCases} total</span>
            </div>
          </div>

          <div className="bg-[#121620] border border-[#1F2637] rounded p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>TRACKED LOSS VOLUME</span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">
              {totalTrackedAmount > 0 ? totalTrackedAmount.toLocaleString() : '0.00'} <span className="text-xs font-normal text-slate-400 font-sans">ETH/USD</span>
            </div>
          </div>

          <div className="bg-[#121620] border border-[#1F2637] rounded p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>SUPPORTED NETWORKS</span>
              <Layers className="w-4 h-4 text-amber-400" />
            </div>
            <div className="mt-2 text-base font-bold font-mono text-slate-200">
              ETH <span className="text-xs text-slate-400">• TRON • BTC • SOL</span>
            </div>
          </div>

          <div className="bg-[#121620] border border-[#1F2637] rounded p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>RPC ENGINE</span>
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            </div>
            <div className="mt-2 text-sm font-bold font-mono text-emerald-400">
              AlchemyProvider <span className="text-xs text-slate-400 block font-normal">HTTP Normalization Active</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#121620] p-3 rounded border border-[#1F2637]">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by case title, case number, or seed address..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#090B10] border border-[#1F2637] rounded pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#090B10] border border-[#1F2637] rounded px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-blue-500 cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="under_investigation">Under Investigation</option>
              <option value="closed">Closed</option>
              <option value="archived">Archived</option>
            </select>

            <select
              value={chainFilter}
              onChange={(e) => setChainFilter(e.target.value)}
              className="bg-[#090B10] border border-[#1F2637] rounded px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-blue-500 cursor-pointer font-mono"
            >
              <option value="all">All Blockchains</option>
              <option value="ethereum">Ethereum</option>
              <option value="tron">Tron</option>
              <option value="bitcoin">Bitcoin</option>
              <option value="solana">Solana</option>
            </select>
          </div>
        </div>

        <div className="bg-[#121620] border border-[#1F2637] rounded overflow-hidden">
          <div className="px-4 py-3 border-b border-[#1F2637] flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
              Investigation Dockets ({filteredCases.length})
            </h2>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-xs text-slate-400 font-mono">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading dockets from database...
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400 font-mono space-y-3">
              <FolderSearch className="w-10 h-10 text-slate-600 mx-auto" />
              <p>No investigation cases found matching the criteria.</p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold cursor-pointer"
              >
                Create First Investigation
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[#0D1017] text-slate-400 border-b border-[#1F2637] font-mono text-[11px]">
                  <tr>
                    <th className="p-3">DOCKET #</th>
                    <th className="p-3">TITLE & TYPOLOGY</th>
                    <th className="p-3">SEED TARGET ADDRESS</th>
                    <th className="p-3">REPORTED LOSS</th>
                    <th className="p-3">CHAIN</th>
                    <th className="p-3">STATUS</th>
                    <th className="p-3 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1F2637]/50 text-slate-300 font-mono">
                  {filteredCases.map((c) => (
                    <tr
                      key={c.case_id}
                      onClick={() => navigate(`/cases/${c.case_id}`)}
                      className="hover:bg-[#161B26] cursor-pointer transition-colors"
                    >
                      <td className="p-3 font-bold text-blue-400">{c.case_number}</td>
                      <td className="p-3">
                        <div className="font-sans font-medium text-slate-100">{c.title}</div>
                        <div className="text-[10px] text-amber-400 uppercase tracking-wider">
                          {c.fraud_type.replace('_', ' ')}
                        </div>
                      </td>
                      <td className="p-3">
                        <AddressDisplay address={c.reported_wallet_address} />
                      </td>
                      <td className="p-3 text-emerald-400 font-bold">
                        {c.reported_amount ? `${Number(c.reported_amount).toLocaleString()} ${c.reported_asset || 'ETH'}` : '—'}
                      </td>
                      <td className="p-3 uppercase text-slate-400">{c.blockchain}</td>
                      <td className="p-3">
                        <StatusBadge status={c.status} />
                      </td>
                      <td className="p-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/cases/${c.case_id}`);
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 border border-blue-500/40 rounded text-[11px] font-semibold transition-colors cursor-pointer"
                        >
                          <span>Workspace</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      <NewCaseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={async (payload) => {
          await createMutation.mutateAsync(payload);
        }}
      />
    </div>
  );
};
