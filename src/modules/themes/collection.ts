import { defineCollection, z } from 'astro:content';

export default defineCollection({
  type: 'content',
  schema: ({image}) => z.object({
    id: z.string(),
    displayName: z.string().optional(),
    tags: z.array(z.string()),
    images: z.array(image()),
    client: z.string().optional(),
    since: z.string().optional(),
  })
});
