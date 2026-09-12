/**
Comment-aware reading of a factory config file.

The example ZXW file carries two whole `<CarDisplayParam>` blocks and two
`<CANBusProtocol>` blocks inside XML comments, so anything that scans for a tag
without understanding comments picks the wrong list. Everything that reads
these files goes through here.
*/

const COMMENT_OPEN = '<!--';
const COMMENT_CLOSE = '-->';

/**
The source with every comment replaced by spaces of the same length, so byte
offsets into the result still point at the same place in the original.
*/
export function blankComments(source: string) {
  let result = '';
  let cursor = 0;

  while (cursor < source.length) {
    const open = source.indexOf(COMMENT_OPEN, cursor);
    if (open === -1) break;

    const close = source.indexOf(COMMENT_CLOSE, open + COMMENT_OPEN.length);
    const end = close === -1 ? source.length : close + COMMENT_CLOSE.length;

    result += source.slice(cursor, open) + ' '.repeat(end - open);
    cursor = end;
  }

  return result + source.slice(cursor);
}

export interface ScalarElement {
  tag: string;
  value: string;
  /**
  Offset of the first byte of the value, i.e. just after `<tag>`.
  */
  valueStart: number;
  /**
  Offset one past the last byte of the value, i.e. at `</tag>`.
  */
  valueEnd: number;
}

const TAG = String.raw`[A-Za-z_][\w.-]*`;
const SCALAR = new RegExp(String.raw`<(${TAG})>([^<]*)</\1>`, 'g');

/**
Every `<tag>value</tag>` leaf outside a comment, keyed by tag name. A tag that
appears more than once maps to every occurrence, so a caller can refuse to act
on an ambiguous name rather than picking the first.
*/
export function findScalarElements(source: string) {
  const blanked = blankComments(source);
  const elements = new Map<string, ScalarElement[]>();

  for (const match of blanked.matchAll(SCALAR)) {
    const [whole, tag, value] = match;
    if (tag === undefined || value === undefined) continue;

    const valueStart = match.index + whole.indexOf('>') + 1;
    const valueEnd = valueStart + value.length;
    // Read the value back out of the original: a comment is never part of one,
    // so the blanked copy only ever supplied the offsets.
    const element: ScalarElement = {
      tag,
      value: source.slice(valueStart, valueEnd),
      valueStart,
      valueEnd
    };

    const found = elements.get(tag);
    if (found) found.push(element);
    else elements.set(tag, [element]);
  }

  return elements;
}
