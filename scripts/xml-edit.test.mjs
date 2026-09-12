import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import { applyEdits, decodeText, encodeText } from '../src/shared/factory-config/xml-edit.ts';
import { blankComments, findScalarElements } from '../src/shared/factory-config/xml-scan.ts';

const FIXTURES = ['public/factory_config.xml', 'public/zxw_factory_config.xml'];

for (const fixture of FIXTURES) {
  const source = readFileSync(fixture, 'utf8');

  test(`${fixture}: no edits changes nothing`, () => {
    assert.equal(applyEdits(source, []).result, source);
  });

  test(`${fixture}: rewriting every value with its own value changes nothing`, () => {
    const edits = findScalarElements(source)
      .entries()
      .filter(([, found]) => found.length === 1)
      .map(([key, found]) => ({ key, value: decodeText(found[0].value) }))
      .toArray();

    const { result, applied, skipped } = applyEdits(source, edits);
    assert.equal(skipped.length, 0);
    assert.equal(applied.length, edits.length);
    assert.equal(result, source);
  });

  test(`${fixture}: one edit changes one substring and nothing else`, () => {
    const [key, found] = findScalarElements(source).entries().next().value;
    const { valueStart, valueEnd } = found[0];
    const expected = `${source.slice(0, valueStart)}changed${source.slice(valueEnd)}`;

    assert.equal(applyEdits(source, [{ key, value: 'changed' }]).result, expected);
  });

  test(`${fixture}: an unknown key is skipped, not guessed`, () => {
    const { result, applied, skipped } = applyEdits(source, [{ key: 'NoSuchKey', value: '1' }]);
    assert.equal(result, source);
    assert.equal(applied.length, 0);
    assert.deepEqual(skipped, [{ key: 'NoSuchKey', value: '1' }]);
  });
}

test('a commented-out block is not mistaken for a live one', () => {
  const source = readFileSync('public/zxw_factory_config.xml', 'utf8');
  // Two of each of these blocks sit inside comments in this file.
  assert.equal(source.split('<CarDisplayParam>').length - 1, 3);
  assert.equal(blankComments(source).split('<CarDisplayParam>').length - 1, 1);
});

test('comments are blanked without moving any other byte', () => {
  const source = '<a>1</a><!-- <b>2</b> --><c>3</c>';
  const blanked = blankComments(source);
  assert.equal(blanked.length, source.length);
  assert.deepEqual([...findScalarElements(source).keys()], ['a', 'c']);
});

test('an unterminated comment swallows the rest of the file', () => {
  assert.deepEqual([...findScalarElements('<a>1</a><!-- <b>2</b>').keys()], ['a']);
});

test('markup characters in a value are escaped on the way in', () => {
  const { result } = applyEdits('<a>1</a>', [{ key: 'a', value: 'x & y < z' }]);
  assert.equal(result, '<a>x &amp; y &lt; z</a>');
  assert.equal(decodeText('x &amp; y &lt; z'), 'x & y < z');
});

test('the vendor punctuation survives a round trip', () => {
  const value = '6.5″ HalfScreen：yes';
  assert.equal(decodeText(encodeText(value)), value);
});

test('a value spanning multiple edits is spliced back to front', () => {
  const source = '<a>111</a><b>2</b><c>33</c>';
  const { result } = applyEdits(source, [
    { key: 'a', value: 'A' },
    { key: 'c', value: 'CCCC' }
  ]);
  assert.equal(result, '<a>A</a><b>2</b><c>CCCC</c>');
});

test('an empty value is written as an empty element body', () => {
  assert.equal(applyEdits('<a>1</a>', [{ key: 'a', value: '' }]).result, '<a></a>');
});

test('a CRLF file keeps its line endings', () => {
  const source = '<root>\r\n  <a>1</a>\r\n</root>';
  assert.equal(
    applyEdits(source, [{ key: 'a', value: '2' }]).result,
    '<root>\r\n  <a>2</a>\r\n</root>'
  );
});

test('a byte order mark is left in place', () => {
  const source = '﻿<a>1</a>';
  assert.equal(applyEdits(source, [{ key: 'a', value: '2' }]).result, '﻿<a>2</a>');
});
