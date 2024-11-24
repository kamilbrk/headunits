import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// https://github.com/colinhacks/zod?tab=readme-ov-file#recursive-types
const BaseSettingItemSchema = z.object({
  name: z.string(),
  nameOld: z.string().optional(),
  description: z.string().optional(),
  configKey: z.string().optional(),
  configValue: z.union([z.string(), z.number()]).optional(),
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
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/factory-settings' }),
  schema: z.object({
    section: z.string(),
    settings: z.array(SettingItemSchema).optional()
  })
});
