import { defineCollection, z } from 'astro:content';

export default defineCollection({
  type: 'content',
  schema: z.object({
    id: z.string(),
    name: z.string(),
    factoryConfigFileName: z.string().optional()
  })
});