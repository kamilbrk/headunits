import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/**
The three controls the car's own screen shows, plus `select` for the settings
whose value is one of a list the config file carries.
*/
const ControlSchema = z.enum(['checkbox', 'radio', 'range', 'select']);

/**
How the value is written back into the XML. The format is untyped, so without
this there is no way to know whether to write `2` or `"BMW_EVO_ID7_V2"`.
*/
const ValueTypeSchema = z.enum(['int', 'string']);

// https://github.com/colinhacks/zod?tab=readme-ov-file#recursive-types
const BaseSettingItemSchema = z.object({
  name: z.string(),
  nameOld: z.string().optional(),
  description: z.string().optional(),
  configKey: z.string().optional(),
  configValue: z.union([z.string(), z.number()]).optional(),
  control: ControlSchema.optional(),
  valueType: ValueTypeSchema.optional(),
  min: z.number().optional(),
  max: z.number().optional(),
  /**
  What a ticked and an unticked box write. Never inferred: the vendor uses
  `0: allow  1: Prohibited` in places, and guessing would silently reverse what
  the reader asked for.
  */
  onValue: z.union([z.string(), z.number()]).optional(),
  offValue: z.union([z.string(), z.number()]).optional(),
  /**
  Documented, but never wired to a live control: the row is an action rather
  than a value, or its meaning is not settled enough to change safely.
  */
  editable: z.boolean().optional(),
  /**
  The key is documented but absent from the example config file in `public/`,
  so we cannot confirm it. It still resolves against a reader's own file.
  */
  unverified: z.boolean().optional(),
  /**
  Shown next to the control. For the vendor's own warnings about values that
  lock you out of factory settings.
  */
  warning: z.string().optional()
});

export type SettingItem = z.infer<typeof BaseSettingItemSchema> & {
  children?: SettingItem[] | undefined;
};

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
