'use strict'

module.exports = {
  parser: 'babel-eslint',

  extends: [
    'standard',
    'plugin:react/recommended',
    'plugin:flowtype/recommended',
  ],

  plugins: [
    'flowtype',
    'react',
  ],

  rules: {
    'camelcase': 'off',
    'comma-dangle': ['error', 'always-multiline'],
    'flowtype/delimiter-dangle': ['error', 'always-multiline'],
    // TODO(mc, 2018-07-24): disabled until fix for crash is released
    // https://github.com/yannickcr/eslint-plugin-react/pull/1860
    'react/prop-types': 'off',
  },

  globals: {},

  env: {
    node: true,
    browser: true,
    jest: true,
  },

  settings: {
    react: {
      version: '16.2',
    },
  },
}
