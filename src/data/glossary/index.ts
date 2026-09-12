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
    aliases: z.array(z.string()).optional(),
    /**
    Skip this term when auto-linking prose. For terms that only ever appear
    inside a larger identifier, or that collide with an ordinary word.
    */
    autolink: z.boolean().default(true)
  })
});
