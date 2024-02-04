import apps from '../modules/apps/collection.ts';
import themes from '../modules/themes/collection.ts';
import updates from '../modules/updates/collection.ts';
import platforms from '../modules/platforms/collection.ts';
import factorySettings from '../modules/factory-settings/collection.ts';
import faq from '../modules/faq/collection.ts';

export const collections = {
  apps,
  'factory-settings': factorySettings,
  themes,
  platforms,
  updates,
  faq
};
