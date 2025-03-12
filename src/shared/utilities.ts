import {type CollectionEntry, type CollectionKey, getCollection, getEntry } from 'astro:content';
import {URL_PREFIX} from "@shared/config.ts";

export const ANDROID_VERSIONS: Record<string, number> = {
  N: 7, // Nougat, New York Cheesecake
  O: 8, // Oreo, Oatmeal Cookie
  P: 9, // Pie, Pistachio Ice Cream
  Q: 10, // Quince Tart
  R: 11, // Red Velvet Cake
  S: 12, // Snow Cone
  T: 13, // Tiramisu
  U: 14, // Upside Down Cake
  V: 15, // Vanilla Ice Cream
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

export type ReferenceOrString = Array<{ collection: string, id: string } | string>;

export type LinkOrText = ({ href: string; text: string }) | string;

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

export function sortEntriesById<E extends CollectionKey>(entryA: CollectionEntry<E>, entryB: CollectionEntry<E>) {
  return entryA.id.localeCompare(entryB.id);
}

export function sortEntriesByDataId<E extends CollectionKey>(entryA: CollectionEntry<E>, entryB: CollectionEntry<E>) {
  return entryA.data.id.localeCompare(entryB.data.id);
}

const REGEX_KSW = /(?:Ksw|Witstek)-([A-Z])-.+v(.+)-ota/;
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
  const entry = entries.sort(sortEntriesByDate).find(entry => entry.id === slug);
  if (!entry) return { entry: undefined, previous: undefined, next: undefined };

  const index = entries.indexOf(entry);
  const next = index === 0 ? undefined : entries[index - 1];
  const previous = index + 1 === entries.length ? undefined : entries[index + 1];
  return { entry, previous, next };
}

export function getVendorSlug(slug: string) {
  return slug.slice(0, slug.indexOf('/'));
}

export function getPlatformSlug(slug: string) {
  return slug.slice(0, slug.lastIndexOf('/'));
}

export async function getUpdateReferences(since: ReferenceOrString = []) {
  return await Promise.all(since.filter(Boolean).map(async ref => {
    const id = typeof ref === 'string' ? ref : ref.id;
    if (!id.includes('/')) return id;

    const entry = await getEntry('updates', id);

    return {
      href: `${URL_PREFIX}updates/${entry.id}`,
      text: `${entry.data.vendor === 'zxw' ? `${entry.data.platform.toUpperCase()} ` : ''}${entry.data.id}`
    };
  }));
}