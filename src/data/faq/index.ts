import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/faq' }),
  schema: z.object({
    question: z.string()
  })
});
