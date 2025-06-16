import globals from "globals";

const { browser, es2021, jest, node } = globals;

export default [
  {
    ignores: ["**/dist/", "node_modules/"],
  },
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...browser,
        ...node,
        ...es2021,
      },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
    },
  },
  {
    files: ["**/*.test.js", "**/jest.setup.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...jest,
        ...browser,
        ...node,
        ...es2021,
        "global": "readonly",
      },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
    },
  },
  {
    files: ["**/*.config.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...node,
        ...es2021,
      },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
    },
  },
];