import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/upgrade-paths' }),
  schema: z.object({
    title: z.string()
  })
});
