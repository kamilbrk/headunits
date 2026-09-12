import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const ModelSchema = z.object({
  /**
  Vendor model designation, e.g. `M600`.
  */
  model: z.string(),
  /**
  Snapdragon marketing name, e.g. `Snapdragon 662`.
  */
  soc: z.string(),
  /**
  Qualcomm part number, e.g. `SM6115`.
  */
  socModel: z.string(),
  cores: z.number().optional(),
  clockGhz: z.number().optional(),
  cpu: z.string().optional()
});

export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/platforms' }),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    models: z.array(ModelSchema).optional(),
    /**
    `ro.board.platform` values seen on this platform.
    */
    boards: z.array(z.string()).optional()
  })
});
