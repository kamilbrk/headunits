import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/glossary' }),
  schema: z.object({
    term: z.string(),
    /**
    Other spellings that mean the same thing.
    */
    aliases: z.array(z.string()).optional()
  })
});
