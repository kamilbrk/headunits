import eslintPluginAstro from 'eslint-plugin-astro';
import eslintPluginPrettierRecommended from 'eslint-plugin-prettier/recommended';
import sonarjs from 'eslint-plugin-sonarjs';
import eslintPluginUnicorn from 'eslint-plugin-unicorn';
import tseslint from 'typescript-eslint';

export default [
  // Ignores (replaces .eslintignore)
  {
    ignores: [
      'node_modules/',
      'dist/',
      'coverage/',
      'test-results/',
      '.astro/',
      '*.tsbuildinfo',
      // eslint-plugin-prettier mis-parses inline <script> content and
      // reports a spurious "Unexpected token" error. `npm run prettier`
      // still formats these files via plain prettier-plugin-astro.
      'src/shared/layout/color-scheme.component.astro',
      'src/shared/layout/navigation.component.astro'
    ]
  },

  // Astro recommended
  ...eslintPluginAstro.configs.recommended,

  // TypeScript — scoped to TS/JS files only so it doesn't override astro parser
  ...tseslint.configs.recommended.map((config) => ({
    ...config,
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx']
  })),

  // SonarJS
  sonarjs.configs.recommended,

  // Unicorn
  eslintPluginUnicorn.configs.recommended,

  // Base rules
  {
    rules: {
      indent: ['error', 2, { SwitchCase: 1 }],
      'linebreak-style': ['error', 'unix'],
      quotes: ['error', 'single'],
      semi: ['error', 'always'],
      'unicorn/filename-case': 'off',
      'unicorn/prevent-abbreviations': 'off',
      'unicorn/no-array-sort': 'off',
      'unicorn/no-array-reverse': 'off',
      'sonarjs/no-nested-template-literals': 'off',
      'sonarjs/no-nested-conditional': 'off',
      'sonarjs/slow-regex': 'warn',
      '@typescript-eslint/triple-slash-reference': 'off'
    }
  },

  // Astro file overrides
  {
    files: ['**/*.astro'],
    rules: {
      'astro/no-conflict-set-directives': 'error',
      'astro/no-unused-define-vars-in-style': 'error'
    }
  },

  // Prettier must be last to override conflicting rules
  eslintPluginPrettierRecommended
];
