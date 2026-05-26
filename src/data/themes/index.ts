import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/themes' }),
  schema: ({ image }) =>
    z.object({
      id: z.string(),
      number: z.number().optional(),
      display: z.string().optional(),
      tags: z.array(z.string()).optional(),
      images: z.array(image()).optional(),
      client: z.string().optional(),
      since: z
        .union([z.array(z.string()), z.string()])
        .optional()
        .transform((val) => (Array.isArray(val) ? val : val ? [val] : [])),
      invalid: z.string().optional()
    })
});
