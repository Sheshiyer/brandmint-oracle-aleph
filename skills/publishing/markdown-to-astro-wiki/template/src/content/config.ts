import { defineCollection, z } from 'astro:content';

const docSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  category: z.string().optional(),
  order: z.number().optional(),
  icon: z.string().optional(),
});

const docs = defineCollection({
  type: 'content',
  schema: docSchema,
});

const frDocs = defineCollection({
  type: 'content',
  schema: docSchema,
});

export const collections = { docs, frDocs };
