export interface DemoMeta {
  demo_data?: boolean;
  [key: string]: unknown;
}

export interface ParsedInvestigatorNotes {
  meta: DemoMeta | null;
  body: string;
}

function parseHeaderLine(line: string): DemoMeta | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith('{') || !trimmed.endsWith('}')) return null;
  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as DemoMeta;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Demo cases prefix `investigator_notes` with a single JSON header line such as
 * `{"demo_data": true, "case_type": "MVP_DEMO", ...}` followed by free text.
 * This splits the header metadata from the human-readable body so the raw JSON
 * never reaches the UI.
 */
export function parseInvestigatorNotes(notes?: string | null): ParsedInvestigatorNotes {
  if (!notes || !notes.trim()) {
    return { meta: null, body: '' };
  }

  const newlineIndex = notes.indexOf('\n');
  const firstLine = newlineIndex === -1 ? notes : notes.slice(0, newlineIndex);
  const rest = newlineIndex === -1 ? '' : notes.slice(newlineIndex + 1);

  const meta = parseHeaderLine(firstLine);
  if (!meta) {
    return { meta: null, body: notes.trim() };
  }

  return { meta, body: rest.trim() };
}

/** Returns investigator notes with any JSON provenance header removed. */
export function stripInvestigatorNotesHeader(notes?: string | null): string {
  return parseInvestigatorNotes(notes).body;
}
