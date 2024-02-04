import { defineCollection, z } from 'astro:content';

// https://github.com/colinhacks/zod?tab=readme-ov-file#recursive-types
const BaseSettingItemSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  control: z.string().optional(),
  min: z.number().optional(),
  max: z.number().optional(),
});
export type SettingItem = z.infer<typeof BaseSettingItemSchema & {
  children?: SettingItem[];
}>;
const SettingItemSchema: z.ZodType<SettingItem> = BaseSettingItemSchema.extend({
  children: z.lazy(() => SettingItemSchema.array().optional())
});

export default defineCollection({
  type: 'content',
  schema: z.object({
    section: z.string(),
    settings: z.array(SettingItemSchema).optional()
  })
});
