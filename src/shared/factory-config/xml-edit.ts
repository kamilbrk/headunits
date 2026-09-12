import { findScalarElements } from './xml-scan.ts';

export interface Edit {
  key: string;
  value: string;
}

/**
XML text has five characters that cannot appear raw. The vendor files use
`&amp;` and nothing else, but a value typed by a reader could contain any of
them.
*/
const ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;'
};

export const encodeText = (value: string) =>
  value.replaceAll(/[&<>]/g, (char) => ESCAPES[char] ?? char);

export const decodeText = (value: string) =>
  value
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&quot;', '"')
    .replaceAll('&apos;', "'")
    .replaceAll('&amp;', '&');

/**
Rewrites the named elements in place and returns the whole file.

Only the bytes between `>` and `</key>` are ever touched — comments,
indentation, attribute spacing, the vendor's full-width punctuation and every
element we do not know about come back exactly as they arrived. Splices run
back to front so earlier offsets stay valid.

An edit naming a key the file does not carry, or carries more than once, is
skipped rather than guessed at; the returned `applied` list says what happened.
*/
export function applyEdits(source: string, edits: readonly Edit[]) {
  const elements = findScalarElements(source);
  const applied: Edit[] = [];
  const skipped: Edit[] = [];

  const splices = [];

  for (const edit of edits) {
    const found = elements.get(edit.key);
    const only = found?.length === 1 ? found[0] : undefined;

    if (!only) {
      skipped.push(edit);
      continue;
    }

    applied.push(edit);
    splices.push({ start: only.valueStart, end: only.valueEnd, text: encodeText(edit.value) });
  }

  const backToFront = splices.toSorted((a, b) => b.start - a.start);
  let result = source;

  for (const splice of backToFront) {
    result = result.slice(0, splice.start) + splice.text + result.slice(splice.end);
  }

  return { result, applied, skipped };
}
