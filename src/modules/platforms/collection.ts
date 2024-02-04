import { defineCollection, reference, z } from 'astro:content';

export default defineCollection({
  type: 'data',
  schema: z.object({
    id: z.string(),
    name: z.string(),
    entries: z.array(reference('updates')).optional()
  })
});
