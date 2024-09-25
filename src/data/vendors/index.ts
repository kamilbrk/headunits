import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export default defineCollection({
  // type: 'content',
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/vendors' }),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    factoryConfigFileName: z.string().optional()
  })
});