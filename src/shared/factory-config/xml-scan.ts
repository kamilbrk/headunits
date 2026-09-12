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

export interface ListItem {
  /**
  Attributes of the item, however they were spaced in the source.
  */
  attributes: Record<string, string>;
  /**
  Text between the tags, empty for a self-closing item.
  */
  text: string;
}

// Scanned rather than matched: the vendor files write both `id="1"` and
// `id = "1"`, and a pattern covering the padding needs two quantifiers side by
// side, which is the shape `sonarjs/super-linear-regex` rejects.
const parseAttributes = (source: string) => {
  const attributes: Record<string, string> = {};
  let cursor = 0;

  while (cursor < source.length) {
    const equals = source.indexOf('=', cursor);
    if (equals === -1) break;

    const open = source.indexOf('"', equals);
    if (open === -1) break;

    const close = source.indexOf('"', open + 1);
    if (close === -1) break;

    const name = source.slice(cursor, equals).trim();
    if (name) attributes[name] = source.slice(open + 1, close);
    cursor = close + 1;
  }

  return attributes;
};

/**
Items of a list section, named as `Parent/Child` — `SupportUIList/Item`,
`CarDisplayParam/model`, `CANBusProtocol/Protocol`.

Returns nothing when the parent is absent, or when the file carries more than
one of it outside a comment: which list was meant would be a guess. The ZXW
example file has three `<CarDisplayParam>` blocks, two of them commented out,
which is what makes the comment handling load-bearing here.
*/
export function findListItems(source: string, path: string): ListItem[] {
  const [parent, child] = path.split('/', 2);
  if (!parent || !child) return [];

  const blanked = blankComments(source);
  const blocks = blanked
    .matchAll(new RegExp(String.raw`<${parent}\b[^>]*>([\s\S]*?)</${parent}>`, 'g'))
    .toArray();
  const only = blocks.length === 1 ? blocks[0] : undefined;
  if (!only) return [];

  const start = only.index + only[0].indexOf('>') + 1;
  const body = source.slice(start, start + (only[1] ?? '').length);
  const items = body
    .matchAll(new RegExp(String.raw`<${child}\b([^>]*?)(?:/>|>([\s\S]*?)</${child}>)`, 'g'))
    .toArray();

  return items.map((item) => ({
    attributes: parseAttributes(item[1] ?? ''),
    text: (item[2] ?? '').trim()
  }));
}
