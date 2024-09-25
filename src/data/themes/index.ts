import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export default defineCollection({
  // type: 'content',
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/themes' }),
  schema: ({image}) => z.object({
    id: z.string(),
    number: z.number().optional(),
    display: z.string().optional(),
    tags: z.array(z.string()).optional(),
    images: z.array(image()).optional(),
    client: z.string().optional(),
    since: z.string().optional(),
    invalid: z.string().optional()
  })
});
