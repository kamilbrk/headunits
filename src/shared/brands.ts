/**
 * Car brands that get their own theme landing page. Keys are theme tags.
 *
 * Deliberately excluded: `common` (vendor-generic UIs, not a car brand) and the
 * modifiers `gs`, `ksw`, `pemp`, `als`, `cusp`, `ls`.
 */
export const THEME_BRANDS: Record<string, string> = {
  bmw: 'BMW',
  benz: 'Mercedes-Benz',
  audi: 'Audi',
  lexus: 'Lexus',
  landrover: 'Land Rover',
  alfaromeo: 'Alfa Romeo'
};
