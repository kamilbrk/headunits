import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export const signaturesSchema = z.object({
  md5: z.string().optional(),
  sha1: z.string().optional(),
  sha256: z.string().optional()
});

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/updates' }),
  schema: z.object({
    id: z.string(),
    vendor: z.string(),
    platform: z.string(),
    date: z.date(),
    android: z.number().optional(),
    version: z.string().optional(),
    signatures: signaturesSchema.optional()
  })
});