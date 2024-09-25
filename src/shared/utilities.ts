import { type CollectionEntry, type CollectionKey, getCollection } from 'astro:content';

export const ANDROID_VERSIONS: Record<string, number> = {
  N: 7,
  O: 8,
  P: 9,
  Q: 10,
  R: 11,
  S: 12,
  T: 13,
  U: 14,
  V: 15
};

export type EntryStaticPath<C extends CollectionKey> = {
  params: { slug: CollectionEntry<C>['id'] },
  props: { entry: CollectionEntry<C> }
}

type CollectionTree<C extends CollectionKey> = {
  [key: string]: CollectionTree<C> | CollectionEntry<C>;
}

type CollectionEntryWithEntries<P extends CollectionKey, C extends CollectionKey> = CollectionEntry<P> & {
  entries: CollectionEntry<C>[];
};

export function getTreeFromCollection<C extends CollectionKey>(collection: CollectionEntry<C>[]) {
  const tree: CollectionTree<C> = {};

  for (const entry of collection) {
    const path = entry.id.split('/');
    let currentNode: CollectionTree<C> = tree;

    for (let i = 0; i < path.length - 1; i++) {
      const part = path[i] as string;

      if (!currentNode.hasOwnProperty(part)) {
        currentNode[part] = {};
      }

      currentNode = currentNode[part] as CollectionTree<C>;
    }

    const leaf = path.at(-1) as string;
    currentNode[leaf] = entry;
  }

  return tree;
}

export async function getEntryStaticPathsFromCollection<C extends CollectionKey>(collectionKey: C): Promise<EntryStaticPath<C>[]> {
  const collection = await getCollection(collectionKey);

  return collection.map(entry => ({
    params: { slug: entry.id },
    props: { entry }
  }));
}

export async function getFirstLevelStaticPathsFromCollection<C extends CollectionKey>(collectionKey: C) {
  const collection = await getCollection(collectionKey);
  const firstLevelSlugs = collection.map(x => x.id.split('/')[0] as string);
  const unique = new Set(firstLevelSlugs);

  return [...unique].map(folder => ({
    params: { slug: folder },
    props: {}
  }));
}

export async function getCollectionGroupedByCollection<C extends CollectionKey, P extends CollectionKey>(
  childrenCollectionKey: C,
  parentsCollectionKey: P,
  filterFn?: (parent: CollectionEntryWithEntries<P, C>) => boolean
) {
  const children = await getCollection(childrenCollectionKey);
  const parents: CollectionEntryWithEntries<P, C>[] = await getCollection(parentsCollectionKey);

  for (const parent of parents) {
    parent.entries = children.filter(entry => entry.id.startsWith(parent.id));
  }
  
  if (filterFn) {
    return parents.reverse().filter(x => filterFn(x));
  }

  return parents;
}

export function sortEntriesByDate<E extends CollectionKey>(entryA: CollectionEntry<E>, entryB: CollectionEntry<E>) {
  return +new Date(entryB.data.date) - +new Date(entryA.data.date);
}

const REGEX_KSW = /Ksw-([A-Z])-.+v(.+)-ota/;
const REGEX_ZXW = /(\d{8})GT_KSW/;

export function getAndroidVersion<E extends CollectionKey>(entry: CollectionEntry<E>) {
  return entry.data.android || ANDROID_VERSIONS[entry.data.id?.match(REGEX_KSW)?.[1]] || '?';
}

export function getUpdateVersion<E extends CollectionKey>(entry: CollectionEntry<E>) {
  return entry.data.version || entry.data.id?.match(REGEX_KSW)?.[2] || entry.data.id?.match(REGEX_ZXW)?.[1] || '?';
}

type CollectionEntryWithPrevNext<C extends CollectionKey> = {
  entry: CollectionEntry<C> | undefined;
  previous: CollectionEntry<C> | undefined;
  next: CollectionEntry<C> | undefined;
}

export async function getEntryWithPrevNext<C extends CollectionKey>(collectionKey: C, slug: string, filter?: (entry: CollectionEntry<C>) => boolean): Promise<CollectionEntryWithPrevNext<C>> {
  const entries = await getCollection(collectionKey, filter);
  const entry = entries.find(entry => entry.id === slug);
  if (!entry) return { entry: undefined, previous: undefined, next: undefined };

  const index = entries.indexOf(entry);
  const previous = index === 0 ? undefined : entries[index - 1];
  const next = index + 1 === entries.length ? undefined : entries[index + 1];
  return { entry, previous, next };
}

export function getVendorSlug(slug: string) {
  return slug.slice(0, slug.indexOf('/'));
}

export function getPlatformSlug(slug: string) {
  return slug.slice(0, slug.lastIndexOf('/'));
}