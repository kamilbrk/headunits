import type { SettingItem } from '../../data/factory-settings';
import type { ScalarElement } from './xml-scan.ts';

import { findListItems, findScalarElements } from './xml-scan.ts';

type Elements = ReadonlyMap<string, readonly ScalarElement[]>;

// A row that never becomes a live control has nothing to get wrong about how
// it would be edited. Whether its key is real still matters.
const isWired = (setting: SettingItem) => setting.editable !== false;

const controlProblems = (setting: SettingItem) => {
  const problems: string[] = [];
  if (!isWired(setting)) return problems;

  if (
    setting.control === 'checkbox' &&
    (setting.onValue === undefined || setting.offValue === undefined)
  ) {
    problems.push('is a checkbox with a key but no onValue/offValue');
  }

  // A key we have never seen tells us nothing about its values either.
  const radios = setting.children?.filter((child) => child.control === 'radio') ?? [];
  if (!setting.unverified && radios.some((child) => child.configValue === undefined)) {
    problems.push('has radio children without a configValue');
  }

  return problems;
};

const optionProblems = (setting: SettingItem, xml: string) => {
  const source = setting.optionsFrom;
  if (!source) return [];

  const items = findListItems(xml, source.path);
  if (items.length === 0) return [`names the list "${source.path}", which resolves to nothing`];

  const missing = items.filter((item) => item.attributes[source.attribute] === undefined);
  if (missing.length > 0) {
    return [`names "${source.attribute}", which ${missing.length} of ${items.length} items lack`];
  }

  const label = source.labelAttribute;
  if (label && items.some((item) => item.attributes[label] === undefined)) {
    return [`names the label "${label}", which not every item in "${source.path}" carries`];
  }

  return [];
};

const keyProblems = (setting: SettingItem, key: string, elements: Elements) => {
  const problems: string[] = [];
  const found = elements.get(key) ?? [];

  if (found.length === 0 && !setting.unverified) {
    problems.push(
      `names "${key}", which is not in the example file. ` +
        'Fix the key, or mark the setting `unverified: true`.'
    );
  }

  if (found.length > 1) problems.push(`names "${key}", which appears ${found.length} times`);

  return problems;
};

/**
Checks the documented `configKey` values against a real config file, at build
time, so a typo or a stale key fails the build instead of quietly rendering a
control that edits nothing.

The two files in `public/` are examples, not a specification, so a key they do
not carry is only an error when the markdown does not already admit it with
`unverified: true`.
*/
export function validateConfigKeys(vendor: string, settings: readonly SettingItem[], xml: string) {
  const elements = findScalarElements(xml);
  const problems: string[] = [];
  const claims = new Map<string, string[]>();

  const visit = (setting: SettingItem, path: string) => {
    const key = setting.configKey;

    if (key) {
      claims.set(key, [...(claims.get(key) ?? []), setting.name]);
      problems.push(
        ...[
          ...controlProblems(setting),
          ...keyProblems(setting, key, elements),
          ...optionProblems(setting, xml)
        ].map((problem) => `${vendor}: ${path} ${problem}`)
      );
    }

    const children = setting.children ?? [];
    for (const child of children) visit(child, `${path} > ${child.name}`);
  };

  for (const setting of settings) visit(setting, setting.name);

  const contested = claims.entries().filter(([, names]) => names.length > 1);
  for (const [key, names] of contested) {
    problems.push(
      `${vendor}: "${key}" is claimed by ${names.length} settings (${names.join(', ')})`
    );
  }

  if (problems.length > 0) {
    throw new Error(`Factory config key mapping is wrong:\n  ${problems.join('\n  ')}`);
  }
}
