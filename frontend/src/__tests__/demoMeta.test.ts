import { describe, it, expect } from 'vitest';
import { parseInvestigatorNotes, stripInvestigatorNotesHeader } from '../lib/demoMeta';

describe('demoMeta investigator_notes parsing', () => {
  it('splits a JSON header line from the human-readable body', () => {
    const notes =
      '{"demo_data": true, "case_type": "MVP_DEMO", "source": "seed"}\nSeed address reported by victim; primary outflow observed at hop 1.';

    const parsed = parseInvestigatorNotes(notes);

    expect(parsed.meta).toEqual({
      demo_data: true,
      case_type: 'MVP_DEMO',
      source: 'seed',
    });
    expect(parsed.body).toBe(
      'Seed address reported by victim; primary outflow observed at hop 1.',
    );
  });

  it('never returns raw JSON in the stripped body', () => {
    const notes = '{"demo_data": true}\nHuman readable description of the case.';

    const body = stripInvestigatorNotesHeader(notes);

    expect(body).not.toContain('demo_data');
    expect(body).toBe('Human readable description of the case.');
  });

  it('returns plain notes untouched when there is no JSON header', () => {
    const notes = 'Plain investigator note without any provenance header.';

    const parsed = parseInvestigatorNotes(notes);

    expect(parsed.meta).toBeNull();
    expect(parsed.body).toBe(notes);
  });

  it('keeps a malformed first line as body content', () => {
    const notes = '{not valid json}\nRemaining text.';

    const parsed = parseInvestigatorNotes(notes);

    expect(parsed.meta).toBeNull();
    expect(parsed.body).toBe('{not valid json}\nRemaining text.');
  });

  it('treats JSON arrays on the first line as non-header content', () => {
    const notes = '["demo_data", true]\nRemaining text.';

    const parsed = parseInvestigatorNotes(notes);

    expect(parsed.meta).toBeNull();
    expect(parsed.body).toBe('["demo_data", true]\nRemaining text.');
  });

  it('handles null and empty notes', () => {
    expect(parseInvestigatorNotes(null)).toEqual({ meta: null, body: '' });
    expect(parseInvestigatorNotes(undefined)).toEqual({ meta: null, body: '' });
    expect(parseInvestigatorNotes('   ')).toEqual({ meta: null, body: '' });
    expect(stripInvestigatorNotesHeader(null)).toBe('');
  });

  it('supports a header-only value with no trailing body', () => {
    const parsed = parseInvestigatorNotes('{"demo_data": true}');

    expect(parsed.meta).toEqual({ demo_data: true });
    expect(parsed.body).toBe('');
  });
});
