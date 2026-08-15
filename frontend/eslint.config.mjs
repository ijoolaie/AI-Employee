import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";
import path from "node:path";

const compat = new FlatCompat({
  baseDirectory: path.dirname(new URL(import.meta.url).pathname),
  recommendedConfig: js.configs.recommended,
});

export default [
  ...compat.extends("next/core-web-vitals"),
  {
    ignores: [".next/**", "out/**", "build/**", "next-env.d.ts", "node_modules/**"],
  },
];
