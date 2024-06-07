import { defineCollection, z } from 'astro:content';

export default defineCollection({
  type: 'content',
  schema: z.object({
    id: z.string(),
    name: z.string(),
    tags: z.array(z.string()).optional(),
    playstore: z.string().optional(),
    website: z.string().optional()
  })
});
