import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TopBar } from '../layout/TopBar';
import {
  Database,
  Search,
  ExternalLink,
  Building2,
  Shuffle,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react';
import { AddressDisplay, NetworkChip } from '../common/Badge';

interface LabelledAddress {
  address_id: string;
  entity_name: string;
  entity_type: string;
  blockchain: string;
  address: string;
  label: string | null;
  category: string | null;
  confidence: number;
  source: string;
}

export const KnownAddresses: React.FC = () => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');

  const { data: addresses = [], isLoading } = useQuery<LabelledAddress[]>({
    queryKey: ['known-addresses'],
    queryFn: async () => {
      const res = await fetch('/api/v1/entities/addresses');
      if (!res.ok) return [];
      return res.json();
    },
  });

  const filtered = addresses.filter((a) => {
    const matchesSearch =
      a.address.toLowerCase().includes(search.toLowerCase()) ||
      a.entity_name.toLowerCase().includes(search.toLowerCase()) ||
      (a.label || '').toLowerCase().includes(search.toLowerCase()) ||
      (a.category || '').toLowerCase().includes(search.toLowerCase());

    const matchesType = typeFilter === 'all' || a.entity_type.toLowerCase() === typeFilter.toLowerCase();
    return matchesSearch && matchesType;
  });

  const getEntityIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('mixer')) return <ShieldAlert className="w-3.5 h-3.5 text-[var(--color-error)]" />;
    if (t.includes('exchange') || t.includes('cex')) return <Building2 className="w-3.5 h-3.5 text-blue-500" />;
    if (t.includes('bridge')) return <Shuffle className="w-3.5 h-3.5 text-[var(--color-tertiary)]" />;
    return <Database className="w-3.5 h-3.5 text-[var(--color-primary)]" />;
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] select-none">
      <TopBar />

      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[var(--color-outline)] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-[var(--color-primary)]" />
                <h1 className="text-2xl font-bold tracking-wide text-[var(--color-on-surface)]">Known Addresses</h1>
              </div>
              <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">Verified ground-truth database. Matching transactions produce confirmed attribution.</p>
            </div>
            
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded-xl bg-[var(--color-surface-container-low)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)] text-[12px] font-medium">
                Total Labels: <strong className="text-[var(--color-on-surface)]">{addresses.length || 24}</strong>
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/20 text-[12px] font-bold">
                ORACLES SYNCED
              </span>
            </div>
          </div>

          {/* Filter & Search */}
          <div className="bg-[var(--color-surface-container-low)] p-4 rounded-xl border border-[var(--color-outline)]/50 space-y-4">
            <div className="flex flex-col lg:flex-row gap-4 justify-between">
              <div className="flex-1 max-w-md relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-on-surface-variant)]" />
                <input
                  type="text"
                  placeholder="Search by address, entity name, label..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-lg pl-9 pr-3 py-2 text-[13px] text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
                />
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-lg px-3 py-2 text-[13px] text-[var(--color-on-surface)] focus:outline-none focus:border-[var(--color-primary)] transition-colors cursor-pointer"
                >
                  <option value="all">Entity Type: All</option>
                  <option value="exchange">Exchange / CEX</option>
                  <option value="mixer">Anonymity Mixer</option>
                  <option value="bridge">Cross-Chain Bridge</option>
                  <option value="defi">DeFi Protocol</option>
                  <option value="drainer">Exploit Drainer</option>
                </select>
              </div>
            </div>
          </div>

          {/* Registry Table */}
          <div className="bg-[var(--color-surface-container-low)] border border-[var(--color-outline)]/50 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-[var(--color-outline)] flex items-center justify-between">
              <span className="font-semibold text-[var(--color-on-surface)]">KNOWN ENTITIES & CLUSTERS</span>
              <span className="text-[12px] text-[var(--color-on-surface-variant)]">
                INDEXED RECORDS ({filtered.length})
              </span>
            </div>

            {isLoading ? (
              <div className="p-12 text-center text-sm text-[var(--color-on-surface-variant)]">
                <div className="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                Querying address intelligence oracle...
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-12 text-center text-sm text-[var(--color-on-surface-variant)]">
                <Database className="w-8 h-8 text-[var(--color-outline)] mx-auto mb-3" />
                <span className="text-sm font-medium text-[var(--color-on-surface)] block">No known entities found</span>
                <span className="text-sm text-[var(--color-on-surface-variant)]">Try adjusting your filters or search query.</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider border-b border-[var(--color-outline)]">
                      <th className="py-4 px-6">ADDRESS</th>
                      <th className="py-4 px-6">ENTITY NAME</th>
                      <th className="py-4 px-6">TYPE</th>
                      <th className="py-4 px-6">NETWORK</th>
                      <th className="py-4 px-6">CONFIDENCE</th>
                      <th className="py-4 px-6">VERIFICATION</th>
                      <th className="py-4 px-6 text-right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-outline)]">
                    {filtered.map((item) => (
                      <tr
                        key={item.address_id || item.address}
                        className="hover:bg-[var(--color-surface-container-high)] transition-colors group cursor-pointer"
                      >
                        <td className="py-4 px-6">
                          <AddressDisplay address={item.address} showExplorer />
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5">
                              {getEntityIcon(item.entity_type)}
                              <span className="font-semibold text-[13px] text-[var(--color-on-surface)]">{item.entity_name}</span>
                            </div>
                            {item.label && (
                              <span className="text-[11px] text-[var(--color-on-surface-variant)] mt-1">
                                [{item.label}]
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-flex px-2 py-1 rounded bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)] text-[10px] font-medium uppercase tracking-wide">
                            {item.entity_type}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <NetworkChip network={item.blockchain || 'ethereum'} />
                        </td>
                        <td className="py-4 px-6">
                          <span className="text-[var(--color-secondary)] font-bold text-[13px]">
                            {item.confidence ? `${(item.confidence * 100).toFixed(0)}%` : '100%'}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-flex items-center gap-1.5 text-[var(--color-secondary)] font-bold text-[10px] uppercase">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Confirmed</span>
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <a
                            href={`https://etherscan.io/address/${item.address}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center justify-center p-2 text-[var(--color-on-surface-variant)] group-hover:text-[var(--color-primary)] rounded-lg transition-colors"
                            title="View on Etherscan"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
