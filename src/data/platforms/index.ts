import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/platforms' }),
  schema: z.object({
    id: z.string(),
    name: z.string()
  })
});
