import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export default defineCollection({
  // type: 'content',
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/apps' }),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    tags: z.array(z.string()).optional(),
    playstore: z.string().optional(),
    website: z.string().optional()
  })
});
