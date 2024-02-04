import { type CollectionEntry, getCollection } from 'astro:content';
import { ANDROID_VERSIONS } from '@/modules/platforms/android.ts';

const regex = /Ksw-(\w)-.+v(.+)-ota/;

export const getUpdatesByPlatform = async () => {
  const allUpdates = await getCollection('updates');
  const allPlatforms = await getCollection('platforms');

  const groups: Record<string, CollectionEntry<'platforms'>> = {};
  const result = [];

  for (const platform of allPlatforms) {
    platform.data.entries = [];
    groups[platform.slug] = platform;
  }

  for (const entry of allUpdates) {
    groups[entry.data.platform.slug]?.data.entries.push(entry);
  }

  for (const group of Object.values(groups)) {
    const numberOfEntriesInGroup = group.data.entries.length;

    group.data.entries = group.data.entries
      .sort((a: any, b: any) => +new Date(b.data.date) - +new Date(a.data.date))
      .map((entry: any, index: number) => {
        const match = entry.data.id.match(regex);
        entry.data.android = ANDROID_VERSIONS[match?.[1]];
        entry.data.version = match?.[2];
        return {
          ...entry,
          previous: index + 1 === numberOfEntriesInGroup ? undefined : group.data.entries[index + 1],
          next: index === 0 ? undefined : group.data.entries[index - 1]
        };
      });

    result.push(group);
  }

  result.sort((a, b) => b.id.localeCompare(a.id));
  return result;
};
