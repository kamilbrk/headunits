import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/platforms' }),
  schema: z.object({
    id: z.string(),
    name: z.string()
  })
});