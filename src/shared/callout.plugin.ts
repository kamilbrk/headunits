import { defineMdastPlugin } from 'satteri';

const KINDS: Record<string, string> = {
  warning: 'Warning',
  note: 'Note'
};

/**
 * Turns a `:::warning` block in Markdown into a styled callout, so a caution
 * can sit next to the instruction it applies to instead of in a footer.
 * Unknown directive names are left alone rather than silently swallowed.
 */
export default defineMdastPlugin({
  name: 'callout',
  containerDirective(node, ctx) {
    const label = KINDS[node.name];
    if (!label) return;

    ctx.replaceNode(node, [
      {
        type: 'html',
        value: `<aside class="callout callout--${node.name}" role="note"><p class="callout__label">${label}</p>`
      },
      ...node.children,
      { type: 'html', value: '</aside>' }
    ]);
  }
});
