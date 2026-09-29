import React, { useEffect, useRef, useState, useCallback } from 'react';
import { api, ApiError } from '../../services/api';
import type { CopilotResponse } from '../../types';
import { ProvenanceBadge } from '../common/ProvenanceBadge';
import {
  Bot,
  Send,
  Clock,
  Cpu,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { useInvestigationStore } from '../../store/investigationStore';

interface CopilotPanelProps {
  caseId: string;
  selectedWalletAddress?: string | null;
  embedded?: boolean;
}

type CopilotAction =
  | { kind: 'ask'; question: string }
  | { kind: 'summarize' }
  | { kind: 'explain_risk'; walletAddress: string };

type ThreadEntry =
  | { id: string; role: 'user'; text: string; timestamp: string }
  | { id: string; role: 'ai'; response: CopilotResponse; timestamp: string }
  | { id: string; role: 'error'; code?: string; message: string; timestamp: string }
  | { id: string; role: 'system'; message: string; timestamp: string };

let entrySeq = 0;
const nextId = () => `copilot-${++entrySeq}`;

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 3000;

const toErrorEntry = (error: unknown): ThreadEntry => {
  const ts = new Date().toLocaleTimeString();
  if (error instanceof ApiError) {
    return {
      id: nextId(),
      role: 'error',
      code: error.code,
      message: error.message,
      timestamp: ts,
    };
  }
  return {
    id: nextId(),
    role: 'error',
    message: error instanceof Error ? error.message : 'Unexpected error',
    timestamp: ts,
  };
};

const toSystemEntry = (message: string): ThreadEntry => ({
  id: nextId(),
  role: 'system',
  message,
  timestamp: new Date().toLocaleTimeString(),
});

export const CopilotPanel: React.FC<CopilotPanelProps> = ({
  caseId,
  selectedWalletAddress,
  embedded = false,
}) => {
  const { language } = useInvestigationStore();
  const [question, setQuestion] = useState('');
  const [thread, setThread] = useState<ThreadEntry[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [thread, isExecuting]);

  const executeAction = useCallback(async (action: CopilotAction) => {
    let attempt = 0;
    
    const tryExecute = async (): Promise<CopilotResponse | null> => {
      try {
        let response: CopilotResponse;
        if (action.kind === 'ask') {
          response = await api.askCopilot(caseId, action.question);
        } else if (action.kind === 'summarize') {
          response = await api.summarizeCase(caseId);
        } else {
          response = await api.explainRisk(caseId, { wallet_address: action.walletAddress });
        }
        return response;
      } catch (error) {
        if (error instanceof ApiError && error.status === 429) {
          if (attempt < MAX_RETRIES) {
            attempt++;
            setRetryCount(attempt);
            setThread((prev) => [...prev, toSystemEntry(
              `AI Provider is currently experiencing high traffic (Rate Limited). Retrying in ${RETRY_DELAY_MS / 1000} seconds... (Attempt ${attempt}/${MAX_RETRIES})`
            )]);
            await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
            return tryExecute();
          }
        }
        throw error;
      }
    };

    try {
      const response = await tryExecute();
      if (response) {
        const ts = new Date().toLocaleTimeString();
        setThread((prev) => [...prev, { id: nextId(), role: 'ai', response, timestamp: ts }]);
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        setThread((prev) => [...prev, toSystemEntry(
          'AI Provider rate limit exceeded after 3 retries. This is a provider capacity issue, not a case data issue. Please try again in a few minutes.'
        )]);
      } else {
        setThread((prev) => [...prev, toErrorEntry(error)]);
      }
    } finally {
      setIsExecuting(false);
      setRetryCount(0);
    }
  }, [caseId]);

  const runAction = (action: CopilotAction) => {
    if (isExecuting) return;
    const promptText =
      action.kind === 'ask'
        ? action.question
        : action.kind === 'summarize'
        ? 'Summarize this case'
        : `Explain risk for wallet ${action.walletAddress}`;
    const ts = new Date().toLocaleTimeString();
    setThread((prev) => [...prev, { id: nextId(), role: 'user', text: promptText, timestamp: ts }]);
    setIsExecuting(true);
    setRetryCount(0);
    executeAction(action);
  };

  const handleAsk = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    setQuestion('');
    runAction({ kind: 'ask', question: trimmed });
  };

  const suggestedActions = [
    { label: language === 'HI' ? 'केस का सारांश दें' : 'Summarize case', action: () => runAction({ kind: 'summarize' }) },
    {
      label: language === 'HI' ? 'जोखिम समझाएं' : 'Explain risk',
      title: selectedWalletAddress
        ? (language === 'HI' ? 'कोपायलट से जोखिम समझाने को कहें' : 'Ask the copilot to explain risk')
        : (language === 'HI' ? 'पहले ग्राफ़ में कोई वॉलेट चुनें' : 'Select a wallet in the graph first'),
      disabled: !selectedWalletAddress,
      action: () =>
        selectedWalletAddress &&
        runAction({
          kind: 'explain_risk',
          walletAddress: selectedWalletAddress,
        }),
    },
    {
      label: language === 'HI' ? 'लेनदेन प्रवाह समझाएं' : 'Explain transaction flow',
      action: () =>
        runAction({
          kind: 'ask',
          question: 'Break down the multi-hop fund flow from the origin address to terminal destinations.',
        }),
    },
    {
      label: language === 'HI' ? 'असामान्य प्रतिपक्षों की पहचान करें' : 'Identify unusual counterparties',
      action: () =>
        runAction({
          kind: 'ask',
          question: 'Identify any mixers, bridge contracts, or flagged exchange addresses in this case.',
        }),
    },
  ];

  return (
    <div className={`flex flex-col h-full min-h-0 bg-[var(--color-surface-dim)] ${embedded ? '' : 'border-l border-[var(--color-outline)]'}`}>
      {/* Copilot Header */}
      <div className="h-14 px-4 bg-[var(--color-surface-dim)] border-b border-[var(--color-outline)] flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
            {language === 'HI' ? 'एआई कोपायलट' : 'AI Copilot'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-[var(--color-on-surface-variant)]">
          <span className="px-2 py-0.5 rounded-md bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] text-purple-400 font-bold tracking-wider">
            QWEN 27B
          </span>
          <ProvenanceBadge variant="ai" size="sm" />
        </div>
      </div>

      {/* Target Context Strip */}
      <div className="px-4 py-2 bg-[var(--color-surface-container-low)] border-b border-[var(--color-outline)] flex items-center justify-between text-[11px] font-semibold text-[var(--color-on-surface-variant)]">
        <div className="flex items-center gap-2 truncate">
          <span className="uppercase tracking-wider">Context:</span>
          <span className="text-[var(--color-on-surface)] font-bold">ID: {caseId.slice(0, 12)}</span>
          {selectedWalletAddress && (
            <>
              <span className="text-[var(--color-on-surface-variant)]">·</span>
              <span className="text-[var(--color-on-surface)] font-bold truncate">
                TARGET: {selectedWalletAddress.slice(0, 8)}...{selectedWalletAddress.slice(-6)}
              </span>
            </>
          )}
        </div>
        <span className="text-[10px] text-[var(--color-secondary)] font-bold uppercase tracking-wider">
          {isExecuting ? (language === 'HI' ? 'निष्पादित हो रहा है...' : 'Executing...') : (language === 'HI' ? 'तैयार' : 'Ready')}
        </span>
      </div>

      {/* Suggested Actions Bar */}
      <div className="p-3 bg-[var(--color-surface-dim)] border-b border-[var(--color-outline)] flex items-center gap-2 overflow-x-auto no-scrollbar shrink-0">
        {suggestedActions.map((s) => (
          <button
            key={s.label}
            onClick={s.action}
            disabled={isExecuting || s.disabled}
            title={s.title}
            type="button"
            className="whitespace-nowrap px-3 py-1.5 rounded-lg bg-[var(--color-surface-container-low)] hover:bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] border border-[var(--color-outline)] text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-50"
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Conversation Thread / Intelligence Cards */}
      <div
        ref={scrollRef}
        className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4"
      >
        {thread.length === 0 && !isExecuting && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3 text-[var(--color-on-surface-variant)]">
            <Cpu className="w-10 h-10 text-purple-400/50" />
            <div>
              <p className="text-sm font-bold text-[var(--color-on-surface)] uppercase tracking-wider">
                {language === 'HI' ? 'केस कोपायलट से पूछें' : 'Ask the Case Copilot'}
              </p>
              <p className="text-xs text-[var(--color-on-surface-variant)] max-w-xs mt-2 leading-relaxed font-medium">
                {language === 'HI' ? 'प्रश्न ऑन-चेन लेनदेन रिकॉर्ड, ग्राफ़ टोपोलॉजी और जोखिम संकेतकों पर आधारित होते हैं। ऊपर दिया गया कोई सुझाया गया प्रश्न चुनें या कोई विशिष्ट विश्लेषणात्मक प्रांप्ट टाइप करें।' : 'Queries are grounded in on-chain transaction records, graph topology, and risk indicators. Select a suggested query above or type a specific analytical prompt.'}
              </p>
            </div>
          </div>
        )}

        {thread.map((entry) => {
          if (entry.role === 'user') {
            return (
              <div key={entry.id} className="flex justify-end">
                <div className="max-w-[85%] p-3 rounded-2xl rounded-tr-sm bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] text-[var(--color-on-surface)] text-xs space-y-1">
                  <div className="flex items-center justify-between text-[10px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-wider">
                    <span>Analyst Query</span>
                    <span>{entry.timestamp}</span>
                  </div>
                  <p className="leading-relaxed font-medium">{entry.text}</p>
                </div>
              </div>
            );
          }

          if (entry.role === 'system') {
            return (
              <div
                key={entry.id}
                className="p-3 rounded-2xl bg-amber-950/20 border border-amber-900/50 text-amber-400 text-xs space-y-2"
              >
                <div className="font-bold flex items-center gap-2 text-[10px] uppercase tracking-wider text-amber-400">
                  <AlertCircle className="w-3 h-3" />
                  <span>System Notice</span>
                  <span>{entry.timestamp}</span>
                </div>
                <p className="font-medium">{entry.message}</p>
              </div>
            );
          }

          if (entry.role === 'error') {
            return (
              <div
                key={entry.id}
                data-testid="copilot-error"
                className="p-3 rounded-2xl bg-red-950/20 border border-red-900/50 text-red-400 text-xs space-y-2"
              >
                <div className="font-bold flex items-center justify-between text-[10px] uppercase tracking-wider text-[var(--color-error)]">
                  <span>Inference Error</span>
                  <span>{entry.timestamp}</span>
                </div>
                {entry.code && (
                  <div className="text-[11px] font-bold text-[var(--color-error)]">{entry.code}</div>
                )}
                <p className="font-medium">{entry.message}</p>
              </div>
            );
          }

          const resp = entry.response;
          return (
            <div
              key={entry.id}
              data-testid="copilot-answer"
              className="p-4 rounded-2xl bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] text-[var(--color-on-surface)] text-xs space-y-3"
            >
              {/* Card Meta Header */}
              <div className="flex items-center justify-between pb-2 border-b border-[var(--color-outline)] text-[11px]">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-purple-400" />
                  <span className="font-bold text-[var(--color-on-surface)] uppercase tracking-wider">Synthesis</span>
                  <span className="text-[var(--color-on-surface-variant)]">·</span>
                  <span className="text-[10px] font-semibold text-[var(--color-on-surface-variant)] tracking-wider">Qwen 27B</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[var(--color-surface-dim)] border border-[var(--color-outline)] text-[10px]">
                    <span className="text-[var(--color-on-surface-variant)] font-semibold uppercase tracking-wider">CONFIDENCE</span>
                    <span className="text-[var(--color-secondary)] font-bold">{(resp.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <span className="text-[10px] text-[var(--color-on-surface-variant)] flex items-center gap-1 font-semibold">
                    <Clock className="w-3 h-3" />
                    {entry.timestamp}
                  </span>
                  <ProvenanceBadge variant="ai" size="sm" />
                </div>
              </div>

              {/* Answer Body */}
              <div className="leading-relaxed whitespace-pre-wrap font-[Inter] text-[13px] text-[var(--color-on-surface)]">
                {resp.type === 'insufficient_data' && !resp.answer ? (
                  <div className="space-y-2 text-[var(--color-on-surface-variant)]">
                    <p className="font-medium">Insufficient case data available to synthesize a factual response.</p>
                    <span className="inline-block px-2 py-1 rounded-md bg-[var(--color-surface-dim)] border border-[var(--color-outline)] text-[11px] font-bold text-[var(--color-on-surface-variant)]">
                      insufficient_data
                    </span>
                  </div>
                ) : (
                  resp.answer
                )}
              </div>

              {/* Citations & Evidence References */}
              {resp.citations && resp.citations.length > 0 && (
                <div className="pt-3 border-t border-[var(--color-outline)] space-y-2">
                  <span className="text-[10px] text-[var(--color-on-surface-variant)] uppercase font-bold tracking-wider block">
                    Citations ({resp.citations.length})
                  </span>
                  <div className="space-y-2">
                    {resp.citations.map((c, i) => (
                      <div
                        key={i}
                        className="p-2 rounded-xl bg-[var(--color-surface-dim)] border border-[var(--color-outline)] flex items-center justify-between text-xs font-medium"
                      >
                        <div className="truncate max-w-[70%]">
                          <span className="text-[var(--color-on-surface-variant)] mr-1.5">[<span className="text-[var(--color-primary)] font-bold">{c.type}</span>]</span>
                          <span className="text-[var(--color-on-surface-variant)]">{c.summary}</span>
                        </div>
                        <span className="text-[var(--color-secondary)] font-bold text-[11px]">
                          {(c.confidence * 100).toFixed(0)}% Match
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {isExecuting && (
          <div className="p-3 rounded-xl bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] flex items-center gap-3 text-[var(--color-on-surface-variant)] text-xs font-medium">
            <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
            <span>
              {retryCount > 0
                ? `Retrying... (${retryCount}/${MAX_RETRIES})`
                : 'Querying Qwen 27B via inference gateway...'}
            </span>
            {retryCount > 0 && (
              <RefreshCw className="w-4 h-4 animate-spin text-[var(--color-tertiary)]" />
            )}
          </div>
        )}
      </div>

      {/* Query Input */}
      <form
        onSubmit={handleAsk}
        className="p-3 bg-[var(--color-surface-dim)] border-t border-[var(--color-outline)] flex items-center gap-3 shrink-0"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={language === 'HI' ? 'इस मामले के बारे में पूछें या फंड प्रवाह के बारे में प्रश्न करें...' : 'Ask about this case or query fund flow...'}
          disabled={isExecuting}
          className="flex-1 bg-[var(--color-surface-container-low)] border border-[var(--color-outline)] rounded-xl px-4 py-2.5 text-xs text-[var(--color-on-surface)] placeholder-[var(--color-on-surface-variant)] focus:outline-none focus:border-[var(--color-primary)] transition-colors font-[Inter] font-medium"
        />
        <button
          type="submit"
          disabled={isExecuting || !question.trim()}
          className="p-2.5 rounded-xl bg-[var(--color-primary)] hover:bg-[#e06810] text-[var(--color-on-surface)] disabled:opacity-50 transition-all cursor-pointer shadow-[0_0_15px_rgba(249,115,22,0.3)] hover:shadow-[0_0_20px_rgba(249,115,22,0.5)]"
          title="Send question"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};