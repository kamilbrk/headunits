import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { InlineCode, Parents, PhrasingContent, Text } from 'mdast';
import type { MdastContent, MdastVisitorContext, PluginFactoryContext } from 'satteri';
import type { AutoLinkDictionary, AutoLinkKind, AutoLinkLabel } from './entity-dictionary';

import { defineMdastPlugin } from 'satteri';

import {
  buildDictionary,
  getEntryHref,
  getGlossaryLabels,
  getUpdateLabels,
  TOKEN_PATTERN
} from './entity-dictionary';

const GLOSSARY_SOURCE = `${path.sep}src${path.sep}data${path.sep}glossary${path.sep}`;

// Entity links stand where an authored link stood, so they keep normal link
// styling and carry no class of their own.
const CLASS_NAMES: Partial<Record<AutoLinkKind, string[]>> = {
  glossary: ['glossary-link']
};

// Code blocks, inline code, image alts, frontmatter and raw HTML are all leaf
// nodes in mdast, so a `text` visitor is never handed their contents and they
// need no check here. Headings and links do need one, and it has to walk the
// ancestors rather than look at the direct parent, because `strong`, `emphasis`
// and `delete` can sit in between.
const SKIP_INSIDE = new Set(['heading', 'link', 'linkReference']);

// Both built once when the Astro config loads, not per document. Inline code
// is matched against entity ids alone: a glossary term inside a code span is
// part of a command or a filename, not prose.
const entityLabels = getUpdateLabels();
const proseDictionary = buildDictionary([...getGlossaryLabels(), ...entityLabels]);
const inlineCodeDictionary = buildDictionary(entityLabels);

interface Match {
  start: number;
  end: number;
  label: AutoLinkLabel;
}

const isInsideSkipped = (node: Readonly<Text | InlineCode>, ctx: MdastVisitorContext) => {
  let current: Readonly<Parents> | undefined = ctx.parent(node);

  while (current) {
    if (SKIP_INSIDE.has(current.type)) return true;
    current = ctx.parent(current);
  }

  return false;
};

/**
 * The longest label that starts at `start` and is still available. A candidate
 * counts only when it ends at a token end too, which is what makes `OTA` miss
 * inside `Ksw-T-M600_OS_v1.6.1-ota`.
 *
 * `claim` is tested last because it records the label it accepts.
 */
const labelAt = (
  value: string,
  start: number,
  labels: readonly AutoLinkLabel[],
  tokenEnds: ReadonlySet<number>,
  claim: (label: AutoLinkLabel) => boolean
) =>
  labels.find(
    (label) =>
      tokenEnds.has(start + label.text.length) &&
      value.startsWith(label.text, start) &&
      claim(label)
  );

/**
 * Left-to-right, non-overlapping, longest label first.
 */
const findMatches = (
  value: string,
  dictionary: AutoLinkDictionary,
  claim: (label: AutoLinkLabel) => boolean
) => {
  const tokens = value.matchAll(TOKEN_PATTERN).toArray();
  const tokenEnds = new Set(tokens.map((token) => token.index + token[0].length));
  const matches: Match[] = [];
  let consumedTo = 0;

  for (const token of tokens) {
    const start = token.index;
    if (start < consumedTo) continue;

    const label = labelAt(value, start, dictionary.get(token[0]) ?? [], tokenEnds, claim);
    if (!label) continue;

    matches.push({ start, end: start + label.text.length, label });
    consumedTo = start + label.text.length;
  }

  return matches;
};

const toLink = (children: PhrasingContent[], label: AutoLinkLabel): MdastContent => {
  const className = CLASS_NAMES[label.kind];

  return {
    type: 'link',
    url: label.href,
    children,
    data: {
      hProperties: { ...(className && { className }), 'data-autolink': label.kind }
    }
  };
};

const splitAroundMatches = (value: string, matches: readonly Match[]) => {
  const nodes: MdastContent[] = [];
  let cursor = 0;

  for (const match of matches) {
    if (match.start > cursor) nodes.push({ type: 'text', value: value.slice(cursor, match.start) });
    nodes.push(toLink([{ type: 'text', value: value.slice(match.start, match.end) }], match.label));
    cursor = match.end;
  }

  if (cursor < value.length) nodes.push({ type: 'text', value: value.slice(cursor) });

  return nodes;
};

/**
 * Links known names in Markdown prose without the author writing the link:
 * the first mention of each glossary term, and every mention of a firmware
 * version id.
 *
 * Glossary terms are linked once per document because a definition only needs
 * reading once. Version ids are linked every time, because each one is an
 * exact identifier the reader may want to follow from wherever they are.
 *
 * Emits root-relative hrefs; `base-path.plugin.ts` adds the base path in the
 * hast phase, which runs after every mdast plugin.
 */
const autoLink = (ctx: PluginFactoryContext) => {
  // MDX would need its own skip rules for JSX text elements, and there are no
  // `.mdx` content files to test them against.
  if (ctx.sourceFormat !== 'markdown') return false;
  if (!ctx.fileURL) return false;
  // The glossary defines these terms; linking them to themselves is noise.
  if (fileURLToPath(ctx.fileURL).includes(GLOSSARY_SOURCE)) return false;

  const selfHref = getEntryHref(fileURLToPath(ctx.fileURL));
  // Resolved once per compiled document, so this is per-document state.
  const linked = new Set<string>();

  const claim = (label: AutoLinkLabel) => {
    // A firmware page linking its own id would point at the page you are on.
    if (label.href === selfHref) return false;
    if (label.kind !== 'glossary') return true;
    if (linked.has(label.href)) return false;

    linked.add(label.href);
    return true;
  };

  return defineMdastPlugin({
    name: 'auto-link',
    text(node, context) {
      if (isInsideSkipped(node, context)) return;

      const matches = findMatches(node.value, proseDictionary, claim);
      if (matches.length === 0) return;

      context.replaceNode(node, splitAroundMatches(node.value, matches));
    },
    // An `inlineCode` node is a leaf and cannot be split, so it is linked only
    // when the whole span is one id. That reproduces what a hand-written
    // [`ID`](/updates/…) renders as, byte for byte.
    inlineCode(node, context) {
      if (isInsideSkipped(node, context)) return;

      const label = inlineCodeDictionary
        .get(node.value)
        ?.find((candidate) => candidate.text === node.value && claim(candidate));
      if (!label) return;

      context.replaceNode(node, toLink([{ type: 'inlineCode', value: node.value }], label));
    }
  });
};

export default autoLink;
