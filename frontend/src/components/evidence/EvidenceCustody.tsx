import React from 'react';
import { TopBar } from '../layout/TopBar';
import { useInvestigationStore } from '../../store/investigationStore';
import { ShieldCheck, Download } from 'lucide-react';

export const EvidenceCustody: React.FC = () => {
  const { evidenceNotes } = useInvestigationStore();

  const handleExportCourtPackage = () => {
    alert('Exporting forensic court package in PDF/ZIP with cryptographic hashes...');
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#090B10]">
      <TopBar title="Chain-of-Custody Evidence Locker" />

      <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-5xl">
        <div className="bg-[#121620] border border-[#1F2637] rounded p-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded bg-emerald-950/60 border border-emerald-700/60 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Evidentiary Preservation Vault</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Cryptographically hashed audit trails and investigator annotations ready for courtroom submission
              </p>
            </div>
          </div>

          <button
            onClick={handleExportCourtPackage}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export Court Package</span>
          </button>
        </div>

        <div className="bg-[#121620] border border-[#1F2637] rounded overflow-hidden">
          <div className="px-4 py-3 border-b border-[#1F2637] font-mono text-xs text-slate-400 font-semibold uppercase">
            Logged Case Notes & Chain of Custody Entries ({evidenceNotes.length})
          </div>
          <div className="p-4 space-y-3">
            {evidenceNotes.map((note) => (
              <div key={note.id} className="p-4 bg-[#090B10] rounded border border-[#1F2637] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">{note.author}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 uppercase">
                      {note.tag || 'LEAD'}
                    </span>
                  </div>
                  <span className="font-mono text-xs text-slate-400">
                    {new Date(note.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{note.content}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};
