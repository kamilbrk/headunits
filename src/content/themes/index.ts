import { defineCollection, z } from 'astro:content';

export default defineCollection({
  type: 'content',
  schema: ({image}) => z.object({
    id: z.string(),
    number: z.number().optional(),
    display: z.string().optional(),
    tags: z.array(z.string()).optional(),
    images: z.array(image()).optional(),
    client: z.string().optional(),
    since: z.string().optional(),
    invalid: z.string().optional()
  })
});
