import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export default defineCollection({
  // type: 'content',
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/faq' }),
  schema: z.object({
    question: z.string()
  })
});
