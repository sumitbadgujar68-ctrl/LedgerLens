import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { RiskSummaryResponse } from '../../types';
import { useInvestigationStore } from '../../store/investigationStore';
import { TopBar } from '../layout/TopBar';
import {
  Download,
  ArrowUpRight,
  ShieldAlert,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const { setNewCaseModalOpen, globalSearchQuery, language } = useInvestigationStore();
  const [statusFilter] = useState('all');
  const [chainFilter, setChainFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');

  const { data: cases = [], isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.getCases(),
  });

  const riskSummaries = useQuery({
    queryKey: ['case-risk-summaries', cases.map(c => c.case_id)],
    queryFn: async () => {
      const results: Record<string, RiskSummaryResponse | null> = {};
      await Promise.all(
        cases.map(async (c) => {
          try {
            const summary = await api.getCaseRiskSummary(c.case_id);
            results[c.case_id] = summary;
          } catch {
            results[c.case_id] = null;
          }
        })
      );
      return results;
    },
    enabled: cases.length > 0,
  });

  const getRiskScore = useCallback((caseId: string): number | null => {
    const summary = riskSummaries.data?.[caseId];
    return summary?.average_score ?? null;
  }, [riskSummaries.data]);

  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      const q = globalSearchQuery ? globalSearchQuery.toLowerCase() : '';
      const matchesSearch =
        !q ||
        c.title.toLowerCase().includes(q) ||
        c.case_number.toLowerCase().includes(q) ||
        c.reported_wallet_address.toLowerCase().includes(q) ||
        c.fraud_type.toLowerCase().includes(q);

      const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
      const matchesChain = chainFilter === 'all' || c.blockchain === chainFilter;

      const riskScore = getRiskScore(c.case_id);
      const matchesRisk =
        riskFilter === 'all'
          ? true
          : riskFilter === 'high'
          ? riskScore !== null && riskScore >= 70
          : riskFilter === 'medium'
          ? riskScore !== null && riskScore >= 40 && riskScore < 70
          : riskScore !== null && riskScore < 40;

      return matchesSearch && matchesStatus && matchesChain && matchesRisk;
    });
  }, [cases, globalSearchQuery, statusFilter, chainFilter, riskFilter, getRiskScore]);

  const handleExportCSV = () => {
    const headers = 'Case Number,Title,Subject Address,Blockchain,Fraud Type,Status,Risk Score,Created At\n';
    const rows = filteredCases
      .map((c) => {
        const riskScore = getRiskScore(c.case_id);
        return `"${c.case_number}","${c.title}","${c.reported_wallet_address}","${c.blockchain}","${c.fraud_type}","${c.status}",${riskScore ?? ''},"${c.created_at}"`;
      })
      .join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `LedgerLens_Cases_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[var(--color-surface-dim)] text-[var(--color-on-surface)] select-none">
      <TopBar
        onNewCase={() => setNewCaseModalOpen(true)}
      />

      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[var(--color-outline)] pb-4">
            <div>
              <h1 className="text-2xl font-bold tracking-wide text-[var(--color-on-surface)]">
                {language === 'HI' ? 'जांच' : 'Investigations'}
              </h1>
              <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">
                {language === 'HI' ? 'चल रही ब्लॉकचेन फोरेंसिक केसों का प्रबंधन और ट्रैक करें।' : 'Manage and track ongoing blockchain forensics cases.'}
              </p>
            </div>
            <button
              onClick={() => setNewCaseModalOpen(true)}
              className="inline-flex items-center gap-2 px-6 py-2 bg-[var(--color-primary)] hover:brightness-110 rounded-xl text-[13px] font-bold text-[var(--color-on-surface)] shadow-sm transition-colors"
            >
              + {language === 'HI' ? 'नया केस' : 'New Case'}
            </button>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { label: language === 'HI' ? 'कुल केस' : 'Total Cases', value: cases.length.toString(), trend: '', color: 'text-[var(--color-secondary)]' },
              { label: language === 'HI' ? 'सक्रिय जांच' : 'Active Investigations', value: cases.filter(c => c.status === 'active' || c.status === 'under_investigation').length.toString(), trend: '', color: 'text-[var(--color-secondary)]' },
              { label: language === 'HI' ? 'गंभीर जोखिम' : 'Critical Risk', value: cases.filter(c => (getRiskScore(c.case_id) ?? 0) >= 70).length.toString(), trend: '', color: 'text-[var(--color-error)]' },
              { label: language === 'HI' ? 'औसत समाधान' : 'Avg Resolution', value: 'N/A', trend: '', color: 'text-[var(--color-on-surface-variant)]' },
            ].map((metric) => (
              <div key={metric.label} className="bg-[var(--color-surface-container-low)] rounded-xl p-5 border border-[var(--color-outline)]/50 flex flex-col justify-between h-32 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-primary)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <span className="text-[13px] text-[var(--color-on-surface-variant)] font-medium">{metric.label}</span>
                <div className="flex items-end justify-between">
                  <span className="text-2xl font-bold text-[var(--color-on-surface)]">{metric.value}</span>
                  <span className={`text-[11px] font-semibold ${metric.color}`}>
                    {metric.trend}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Filters & Search */}
          <div className="bg-[var(--color-surface-container-low)] p-4 rounded-xl border border-[var(--color-outline)]/50 space-y-4">
            <div className="flex flex-col lg:flex-row justify-between gap-4">
              <div className="flex items-center gap-2 overflow-x-auto hide-scrollbar">
                <div className="flex items-center gap-1 bg-[var(--color-surface-dim)] p-1 rounded-lg border border-[var(--color-outline)]">
                  <button onClick={() => setChainFilter('all')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap ${chainFilter === 'all' ? 'bg-[var(--color-surface-container-high)] text-[var(--color-primary)]' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}>{language === 'HI' ? 'सभी चेन' : 'All Chains'}</button>
                  <button onClick={() => setChainFilter('ethereum')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap ${chainFilter === 'ethereum' ? 'bg-[var(--color-surface-container-high)] text-[var(--color-primary)]' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}>Ethereum</button>
                </div>

                <div className="flex items-center gap-1 bg-[var(--color-surface-dim)] p-1 rounded-lg border border-[var(--color-outline)]">
                  <button onClick={() => setRiskFilter('all')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap ${riskFilter === 'all' ? 'bg-[var(--color-surface-container-high)] text-[var(--color-primary)]' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}>{language === 'HI' ? 'सभी जोखिम' : 'All Risks'}</button>
                  <button onClick={() => setRiskFilter('high')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap ${riskFilter === 'high' ? 'bg-[var(--color-surface-container-high)] text-[var(--color-error)]' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}>{language === 'HI' ? 'उच्च जोखिम' : 'High Risk'}</button>
                  <button onClick={() => setRiskFilter('medium')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap ${riskFilter === 'medium' ? 'bg-[var(--color-surface-container-high)] text-[var(--color-tertiary)]' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)]'}`}>{language === 'HI' ? 'मध्यम जोखिम' : 'Medium Risk'}</button>
                </div>
              </div>

              <div className="flex gap-2">
                {/* Search is now in the global TopNav */}
                <button
                  onClick={handleExportCSV}
                  className="flex items-center justify-center p-2 bg-[var(--color-surface-dim)] border border-[var(--color-outline)] rounded-lg text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:border-[var(--color-primary)] transition-colors"
                  title="Export Report"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Cases Table */}
          <div className="bg-[var(--color-surface-container-low)] rounded-xl border border-[var(--color-outline)]/50 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-[11px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider border-b border-[var(--color-outline)]">
                    <th className="px-6 py-4">{language === 'HI' ? 'केस विवरण' : 'Case Details'}</th>
                    <th className="px-6 py-4">{language === 'HI' ? 'लक्ष्य इकाई' : 'Target Entity'}</th>
                    <th className="px-6 py-4">{language === 'HI' ? 'नेटवर्क' : 'Network'}</th>
                    <th className="px-6 py-4">{language === 'HI' ? 'जोखिम स्कोर' : 'Risk Score'}</th>
                    <th className="px-6 py-4">{language === 'HI' ? 'स्थिति' : 'Status'}</th>
                    <th className="px-6 py-4 text-right">{language === 'HI' ? 'कार्रवाई' : 'Actions'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-outline)]">
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center">
                        <div className="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                        <span className="text-sm text-[var(--color-on-surface-variant)]">{language === 'HI' ? 'केस लोड हो रहे हैं...' : 'Loading cases...'}</span>
                      </td>
                    </tr>
                  ) : filteredCases.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center">
                        <ShieldAlert className="w-8 h-8 text-[var(--color-outline)] mx-auto mb-3" />
                        <span className="text-sm font-medium text-[var(--color-on-surface)] block">{language === 'HI' ? 'कोई केस नहीं मिला' : 'No cases found'}</span>
                        <span className="text-sm text-[var(--color-on-surface-variant)]">{language === 'HI' ? 'अपने फ़िल्टर या खोज क्वेरी को समायोजित करने का प्रयास करें।' : 'Try adjusting your filters or search query.'}</span>
                      </td>
                    </tr>
                  ) : (
                    filteredCases.map((c) => {
                      const riskScore = getRiskScore(c.case_id);
                      const fraudTypeLabel = c.fraud_type.replace(/_/g, ' ');
                      
                      return (
                        <tr 
                          key={c.case_id}
                          onClick={() => navigate(`/cases/${c.case_id}`)}
                          className="hover:bg-[var(--color-surface-container-high)] cursor-pointer transition-colors group"
                        >
                          <td className="px-6 py-4">
                            <div className="flex flex-col">
                              <span className="text-[13px] font-semibold text-[var(--color-on-surface)]">{c.case_number}</span>
                              <span className="text-[11px] text-[var(--color-on-surface-variant)] mt-1">{new Date(c.created_at).toLocaleDateString()}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex flex-col">
                              <span className="text-[13px] font-semibold text-[var(--color-on-surface)] truncate max-w-[200px]">{c.title}</span>
                              <span className="text-[11px] text-[var(--color-on-surface-variant)] font-bold mt-1 truncate max-w-[200px]">{c.reported_wallet_address}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              {c.blockchain === 'ethereum' && <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />}
                              {c.blockchain === 'bitcoin' && <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)]" />}
                              {c.blockchain !== 'ethereum' && c.blockchain !== 'bitcoin' && <div className="w-1.5 h-1.5 rounded-full bg-red-500" />}
                              <span className="text-[13px] font-medium text-[var(--color-on-surface)]">
                                {c.blockchain === 'ethereum' ? 'Ethereum' : c.blockchain === 'bitcoin' ? 'Bitcoin' : 'Tron'}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              {riskScore !== null ? (
                                <span className={`inline-flex items-center justify-center w-7 h-7 rounded text-[11px] font-bold ${
                                  riskScore >= 70 ? 'bg-[var(--color-error)]/10 text-[var(--color-error)]' : 
                                  riskScore >= 40 ? 'bg-[var(--color-tertiary)]/10 text-[var(--color-tertiary)]' : 
                                  'bg-[var(--color-secondary)]/10 text-[var(--color-secondary)]'
                                }`}>
                                  {riskScore}
                                </span>
                              ) : (
                                <span className="inline-flex items-center justify-center w-7 h-7 rounded text-[11px] font-bold bg-[var(--color-surface-dim)] text-[var(--color-on-surface-variant)] border border-[var(--color-outline)]">
                                  —
                                </span>
                              )}
                              <span className="text-[12px] text-[var(--color-on-surface-variant)] truncate max-w-[120px] hidden lg:block capitalize">
                                {fraudTypeLabel}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-bold tracking-wide uppercase ${
                              c.status === 'active' ? 'text-[var(--color-secondary)] bg-[var(--color-secondary)]/10' : 
                              c.status === 'under_investigation' ? 'text-[var(--color-tertiary)] bg-[var(--color-tertiary)]/10' : 
                              'text-gray-400 bg-gray-500/10'
                            }`}>
                              {c.status === 'active' ? (language === 'HI' ? 'सक्रिय' : 'Active') : c.status === 'under_investigation' ? (language === 'HI' ? 'जांच जारी' : 'Investigating') : (language === 'HI' ? 'बंद' : 'Closed')}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button className="inline-flex items-center justify-center p-2 text-[var(--color-on-surface-variant)] group-hover:text-[var(--color-primary)] rounded-lg transition-colors">
                              <ArrowUpRight className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            
            {/* Pagination / Footer */}
            {!isLoading && filteredCases.length > 0 && (
              <div className="px-6 py-3 border-t border-[var(--color-outline)] bg-[var(--color-surface-dim)] flex items-center justify-between">
                <span className="text-[12px] text-[var(--color-on-surface-variant)]">
                  Showing <span className="font-semibold text-[var(--color-on-surface)]">{filteredCases.length}</span> active cases
                </span>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};