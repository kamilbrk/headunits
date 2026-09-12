import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

export const signaturesSchema = z.object({
  md5: z.string().optional(),
  sha1: z.string().optional(),
  sha256: z.string().optional()
});

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.{md,mdx}', base: './src/data/updates' }),
  schema: z.object({
    id: z.string(),
    vendor: z.string(),
    platform: z.string(),
    date: z.date(),
    android: z.number().optional(),
    version: z.string().optional(),
    signatures: signaturesSchema.optional(),
    // Overrides the comparison baseline for the generated "Changes since"
    // sentence, for the few builds whose real baseline is not the previous
    // entry on the same platform. Values are collection ids.
    comparedTo: z.array(z.string()).optional()
  })
});
