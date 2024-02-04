import { defineCollection, reference, z } from 'astro:content';

export const signaturesSchema = z.object({
  sha1: z.string().optional(),
  sha256: z.string().optional(),
  md5: z.string().optional()
});

export default defineCollection({
  type: 'content',
  schema: z.object({
    id: z.string().startsWith('Ksw-').endsWith('-ota'),
    platform: reference('platforms'),
    date: z.string().datetime({ precision: 0 }),
    signatures: signaturesSchema.optional()
  })
});
